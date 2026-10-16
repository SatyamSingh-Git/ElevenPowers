"""Independent grades remain comparable when installed feedback fails to arrive."""
import importlib.util
import json
from pathlib import Path

import pytest

from eval import preservation as p
from eval.workflow_cases import case
from eval.workflow_oracles import grade


def api():
    assert importlib.util.find_spec('eval.workflow_results'),'four-stage result accounting is missing'
    from eval import workflow_results
    return workflow_results


def groups(states):
    return {'state':'graded','groups':[{'id':key,'introduced_stage':introduced,'state':state}
        for key,introduced,state in states]}


def test_previously_failing_feature_is_not_a_new_regression():
    r=api()
    before=groups([('core',0,'passed'),('lease',1,'failed')])
    after=groups([('core',0,'failed'),('lease',1,'failed'),('restart',2,'failed')])
    assert r.metrics(before,after,2)=={'regressed':['core'],'earlier_failed':['core','lease'],'new_failed':['restart']}
    assert r.metrics(None,after,2)['regressed'] is None


@pytest.fixture
def batch(tmp_path):
    root=tmp_path/'batch';protocol=p.prepare(root,names=('workflow-queue-py',),seconds=720)
    value=case('workflow-queue-py')
    for slot in protocol['slots']:
        folder=root/slot;candidate=folder/'candidate';stages=[]
        for stage,cap in enumerate((180,239.9666666667,359.9,719.7),1):
            (candidate/'service.py').write_text(value['gold'][3],encoding='utf8')
            source={n:(candidate/n).read_bytes().decode('utf8') for n in value['production']}
            p._write(folder/f'source-{stage}.json',source)
            stages.append({'stage':stage,'state':'completed','scope':'preserved','seconds_cap':cap,'elapsed_ms':100,
                'conversation_identity':protocol['seals'][slot]['session'],
                'host_observation':{'completed':True,'models':['claude-sonnet-5-5']},
                'source_after':p._manifest(candidate),'independent_grade':grade(value,stage,candidate),
                'native':{'state':'incomplete','native_runner_adoption':False}})
        p._write(folder/'result.json',{'schema':2,'slot':slot,'state':'completed','model_seconds':0.4,'stages':stages})
    return root,protocol


def test_failed_delivery_does_not_drop_a_graded_pair(batch):
    api();root,protocol=batch
    result=p.summarize(root)
    assert result['scheduled']==2 and result['attempted']==2
    pair=result['pairs'][0]
    assert pair['outcome_comparable'] is True and pair['delivery_verified'] is False
    assert pair['difference']==0 and result['paired_correctness_advantage_observed'] is False


@pytest.mark.parametrize('defect',['timeout','missing_stage','wrong_session','source_drift'])
def test_incomplete_or_unidentified_attempts_stay_in_denominator(batch,defect):
    api();root,protocol=batch;slot=protocol['slots'][1];folder=root/slot
    record=p._read(folder/'result.json')
    if defect=='timeout':record['stages'][-1]['state']='timeout'
    elif defect=='missing_stage':record['stages'].pop()
    elif defect=='wrong_session':record['stages'][-1]['conversation_identity']='wrong'
    else:
        source=p._read(folder/'source-4.json');source['service.py']+='\n# drift\n';p._write(folder/'source-4.json',source)
    p._write(folder/'result.json',record)
    result=p.summarize(root)
    assert result['scheduled']==2 and result['attempted']==2
    assert result['pairs'][0]['outcome_comparable'] is False
    assert result['pairs'][0]['difference'] is None


def test_archive_reproduces_sources_without_models(batch,tmp_path):
    api();root,protocol=batch
    from eval.preservation_archive import publish
    archive=tmp_path/'public'
    result=publish(archive,{slot:root for slot in protocol['slots']})
    assert result['state']=='regraded'
    assert len(list(archive.glob('*-evidence.json')))==2
    reproduced=api().reproduce(archive)
    assert reproduced['qualified'] and reproduced['stages']==8
    raw='\n'.join(f.read_text(encoding='utf8') for f in archive.glob('*.json'))
    assert str(tmp_path) not in raw
    source_file=next(archive.glob('*source-4.json'))
    changed=json.loads(source_file.read_text());changed['service.py']+='\n# tamper\n';source_file.write_text(json.dumps(changed))
    assert not api().reproduce(archive)['qualified']


@pytest.mark.parametrize('arm',['ordinary','assisted'])
def test_observed_advantage_and_worse_outcomes_are_both_retained(batch,arm):
    api();root,protocol=batch;slot=next(s for s in protocol['slots'] if s.endswith('-'+arm));folder=root/slot;candidate=folder/'candidate'
    value=case('workflow-queue-py');(candidate/'service.py').write_text(value['fault'][0],encoding='utf8')
    record=p._read(folder/'result.json');last=record['stages'][-1]
    last['source_after']=p._manifest(candidate);last['independent_grade']=grade(value,4,candidate)
    p._write(folder/'source-4.json',{n:(candidate/n).read_bytes().decode('utf8') for n in value['production']})
    p._write(folder/'result.json',record)
    result=p.summarize(root)
    assert result['pairs'][0]['difference']*(1 if arm=='ordinary' else -1)>0
    assert result['pairs'][0][arm]['stages'][-1]['regressed']==['lease_expiry','restart_fencing']


def test_archive_cannot_qualify_after_a_scheduled_source_row_is_removed(batch,tmp_path):
    root,protocol=batch
    from eval.preservation_archive import publish
    archive=tmp_path/'public';publish(archive,{slot:root for slot in protocol['slots']})
    manifest=p._read(archive/'manifest.json');manifest['sources'].pop();p._write(archive/'manifest.json',manifest)
    assert api().reproduce(archive)['qualified'] is False


def test_source_regrading_does_not_claim_historical_harness_execution(batch,tmp_path):
    root,protocol=batch
    from eval.preservation_archive import publish
    archive=tmp_path/'public';publish(archive,{slot:root for slot in protocol['slots']})
    manifest=p._read(archive/'manifest.json');manifest['harness_sha256']='0'*64;p._write(archive/'manifest.json',manifest)
    result=api().reproduce(archive)
    assert result['qualified'] and result['grading_only']
    assert result['historical_harness_matches'] is False


@pytest.mark.parametrize('late_defect',['protected_test','source_snapshot'])
def test_late_integrity_failure_retains_earlier_regression_and_time(batch,late_defect):
    root,protocol=batch;slot=protocol['slots'][1];folder=root/slot;candidate=folder/'candidate'
    value=case('workflow-queue-py');record=p._read(folder/'result.json')
    (candidate/'service.py').write_text(value['fault'][0],encoding='utf8')
    earlier=record['stages'][2]
    earlier['source_after']=p._manifest(candidate)
    earlier['independent_grade']=grade(value,3,candidate)
    p._write(folder/'source-3.json',{n:(candidate/n).read_bytes().decode('utf8') for n in value['production']})
    (candidate/'service.py').write_text(value['gold'][3],encoding='utf8')
    if late_defect=='protected_test':
        public=next((candidate/'tests').glob('test_*.py'));public.write_text('# changed protected test\n')
    else:
        (folder/'source-4.json').write_text('{')
    p._write(folder/'result.json',record)
    result=p.summarize(root);arm=result['pairs'][0]['assisted']
    assert result['outcome_comparable'] is False and arm['qualified'] is False
    assert arm['model_seconds']==0.4
    assert len(arm['stages'])==4
    assert arm['stages'][2]['regressed']==['lease_expiry','restart_fencing']
    assert arm['stages'][2]['source_grade_valid'] is True
    assert arm['issues']
