"""Published failures and source grades stay reproducible without model calls."""
import importlib.util
import json

import pytest


def test_hard_archive_reader_exists():
    assert importlib.util.find_spec('eval.hard_archive') is not None, 'hard archive reader is missing'


def test_failed_attempts_survive_archive_and_cannot_be_qualified(tmp_path):
    from eval import benefit, hard_archive, hard_cases, proposals
    root=tmp_path/'batch'
    protocol=benefit.prepare_batch(root,seconds=480,suite=hard_cases,repeats=1,model='claude-sonnet-5')
    (root/'attempt.json').write_text(json.dumps({'schema_version':1,'state':'finished','phase':'coding_calls','runs':8}))
    for c,n,a in benefit.schedule(suite=hard_cases,repeats=1):
        candidate=root/f'{c}-{n}-{a}'
        snap=proposals.snapshot(candidate,hard_cases.names(c))
        grade=hard_cases.grade(c,candidate)
        record={'schema_version':1,'case':c,'replicate':n,'arm':a,'state':'host_failed','initial_grade':grade,
                'final_grade':grade,'proposals':[],'model':protocol['model'],'effort':'medium','elapsed_ms':1,
                'exit_code':1,'observation':None,'callbacks':{},'final_snapshot':snap}
        (root/f'{candidate.name}-result.json').write_text(json.dumps(record))
    destination=tmp_path/'archive.json';hard_archive.publish(root,destination)
    result=hard_archive.inspect(destination)
    assert result['summary']['state']=='inconclusive' and result['summary']['valid_runs']==0
    assert not result['summary']['coding_improvement_observed']
    value=json.loads(destination.read_text())
    value['schema_version']=2;value['prior_attempt']={**value['attempt'],'state':'running'}
    value['attempt'].update(prior_attempt_preserved=True,recorded_harness=protocol['harness_fingerprint'],execution_harness=protocol['harness_fingerprint'],controller_pid=1)
    value['runs'][0]['record'].update(state='interrupted',elapsed_ms=None,exit_code=None)
    destination.write_text(json.dumps(value))
    result=hard_archive.inspect(destination)
    assert result['summary']['state']=='inconclusive' and result['summary']['runs']==8
    value=json.loads(destination.read_text());value['runs'].append(value['runs'][0]);destination.write_text(json.dumps(value))
    with pytest.raises(ValueError):hard_archive.inspect(destination)


def test_archive_rejects_forged_grade_without_running_candidate(tmp_path):
    from eval import hard_archive, hard_cases
    names=[r[0] for r in __import__('eval.hard_scenarios',fromlist=['SCENARIOS']).SCENARIOS['lease-queue']()]
    value={'state':'graded','passed':len(names),'total':len(names),'checks':dict.fromkeys(names,False),'regressions':0}
    assert not hard_archive.valid_grade('lease-queue',value)
