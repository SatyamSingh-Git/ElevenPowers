"""Forward references and contract-breaking faults pin independent stage grading."""
import importlib.util
from pathlib import Path
import shutil

import pytest


def api():
    assert importlib.util.find_spec('eval.workflow_cases'), 'four-stage cases missing'
    from eval.workflow_cases import case
    from eval.workflow_oracles import grade
    return case,grade


def materialize(root,value,source=None):
    root.mkdir()
    for name,text in value['files'].items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf8')
    if source is not None: (root/value['production'][0]).write_text(source,encoding='utf8')
    return root


@pytest.fixture(params=['workflow-queue-py','workflow-orders-js'])
def value(request):
    if request.param.endswith('js') and not shutil.which('node'): pytest.skip('Node unavailable')
    case,_=api()
    return case(request.param)


def test_initial_project_runs_core_but_does_not_already_solve_first_feature(tmp_path,value):
    _,grade=api();root=materialize(tmp_path/'initial',value)
    base=grade(value,0,root);first=grade(value,1,root)
    assert base['state']=='graded' and base['passed']==2 and base['failed']==0
    assert first['state']=='graded' and first['failed']>0


def test_four_stage_group_counts_are_cumulative(tmp_path,value):
    _,grade=api();root=materialize(tmp_path/'reference',value,value['gold'][3])
    results=[grade(value,s,root) for s in range(5)]
    assert [len(r['groups']) for r in results]==[2,4,6,8,10]
    assert all(r['state']=='graded' and r['failed']==0 for r in results)
    assert len(value['requests'])==4


@pytest.mark.parametrize('stage',[1,2,3,4])
def test_each_fault_fails_its_intended_behavior_group(tmp_path,value,stage):
    _,grade=api();root=materialize(tmp_path/'fault',value,value['fault'][stage-1])
    result=grade(value,stage,root)
    assert result['state']=='graded',result
    assert result['failed']>=1
    groups={g['id']:g['state'] for g in result['groups']}
    assert groups[value['fault_groups'][stage-1]]=='failed'


def test_grader_accepts_source_formatting_and_rejects_missing_inputs(tmp_path,value):
    _,grade=api();root=materialize(tmp_path/'formatted',value,value['gold'][3]+'\n# formatting\n' if value['language']=='python' else value['gold'][3]+'\n// formatting\n')
    result=grade(value,4,root)
    assert result['state']=='graded' and result['failed']==0
    (root/value['production'][0]).unlink()
    assert grade(value,4,root)['state']=='incomplete'


def test_case_dispatch_preserves_existing_frozen_cases():
    api()
    from eval.preservation_cases import case
    assert len(case('queue')['requests'])==2
    assert len(case('workflow-queue-py')['requests'])==4
    with pytest.raises(ValueError): case('../project')


def test_python_v2_snapshot_requires_fields_and_oracle_detects_missing_field_default(tmp_path):
    import json
    case,grade=api();value=case('workflow-queue-py');namespace={}
    exec(value['gold'][3],namespace)
    snapshot=json.loads(namespace['Queue']().dumps())
    for field in ('max_attempts','seen','serial','items'):
        bad=dict(snapshot);bad.pop(field)
        with pytest.raises(ValueError):namespace['Queue'].loads(json.dumps(bad))
    mutant=value['gold'][3].replace('if value["version"] == 2:', 'if False:')
    root=materialize(tmp_path/'missing-fields-mutant',value,mutant)
    result=grade(value,2,root)
    assert result['state']=='graded'
    assert next(g['state'] for g in result['groups'] if g['id']=='snapshot_validation')=='failed'
