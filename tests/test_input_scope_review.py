"""Final-review regressions use real consumers and saved execution state."""
import json

from core.config import Config, save
from core.inputs.receipts import inspect
from core.patchproof.execution import verify
from core.patchproof.planning import plan
from tests.test_external_input_reuse import dependency_project
from tests.test_input_scopes import scoped_project, observed_run
from tests.test_patchproof_identity import commit


def test_sanitized_mapping_cannot_match_a_different_secret_command(scoped_project):
    root,target,other,commands,args,policy=scoped_project
    actual=commands[0]+' token=fixture-private1'
    save(root,Config(auto_detect=False,commands={'tests':actual,'build':commands[1]}))
    policy['commands'][0]['command']=commands[0]+' token=REDACTED'
    (root/'elevenpowers.inputs.json').write_text(json.dumps(policy))
    code,records=observed_run(root,actual)
    assert code==0
    other.unlink()
    assert inspect(records[-1],root)['state']=='incomplete'


def test_missing_required_input_retains_independent_saved_execution(scoped_project):
    root,target,other,commands,*_=scoped_project
    base=commit(root,'two explicit scopes')
    (root/'service.py').write_text('value=3\n')
    head=commit(root,'service change')
    first=verify(root,base,head,seconds=180)
    assert first['state']=='passed',first['issues']
    target.unlink()
    current=plan(root,base,head,seconds=180)
    assert not current['ready'],'missing required first command still prevents complete verification'
    actions={row['properties'][0]:row['action'] for row in current['checks']}
    assert actions=={'tests':'run','build':'reuse'},current['bundle']['execution']
    assert not any('patch, checkout or source changed' in issue for issue in current['issues'])


def test_late_guard_clears_saved_external_associations(scoped_project,monkeypatch):
    from core.patchproof import report as patch_report
    root,target,other,commands,*_=scoped_project
    base=commit(root,'two explicit scopes')
    (root/'service.py').write_text('value=3\n')
    head=commit(root,'service change')
    assert verify(root,base,head,seconds=180)['state']=='passed'
    original=patch_report.verification_report
    calls=0
    def late(root,**kwargs):
        nonlocal calls
        calls+=1
        value=original(root,**kwargs)
        if calls==3:
            target.write_text('value=9\n' if target.suffix=='.py' else 'module.exports={value:9};\n')
        return value
    monkeypatch.setattr(patch_report,'verification_report',late)
    current=patch_report.build(root,base,head,timeout=180)
    assert current['binding']['state']=='unavailable'
    assert current['execution']['checks']
    assert all(c['external_inputs_association']=='unavailable' for c in current['execution']['checks'])


def test_unused_missing_witness_does_not_block_required_command(scoped_project):
    root,target,other,commands,*_=scoped_project
    save(root,Config(auto_detect=False,commands={'build':commands[1]}))
    base=commit(root,'only independent build is required')
    (root/'service.py').write_text('value=3\n')
    head=commit(root,'service change')
    target.unlink()
    current=plan(root,base,head,seconds=180)
    assert current['ready'],current['issues']
    assert current['bundle']['external_inputs']['state']=='incomplete'
    assert verify(root,base,head,seconds=180)['state']=='passed'
    current=plan(root,base,head,seconds=180)
    assert current['ready'],current['issues']
    assert [row['action'] for row in current['checks']]==['reuse']
