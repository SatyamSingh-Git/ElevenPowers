"""Installed adoption needs native calls and owned receipts, never a final claim."""
import importlib.util
import json
from pathlib import Path
import shutil
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]


def api():
    assert importlib.util.find_spec('eval.declared_workflow'), 'declared workflow adapter is missing'
    from eval import declared_workflow
    return declared_workflow


@pytest.mark.parametrize('language', ['python', 'javascript'])
def test_rehearsal_never_launches_models(tmp_path, language, monkeypatch):
    if language == 'javascript' and not shutil.which('node'):
        pytest.skip('Node unavailable')
    from eval import subscription, input_scope_pilot
    monkeypatch.setattr(subscription, 'auth', lambda *a: pytest.fail('model authentication in rehearsal'))
    value = input_scope_pilot.pilot(tmp_path/'new', language, ROOT, protocol='declared-runner',
                                    seconds=240, rehearse=True)
    assert value['model_calls'] == 0 and value['qualified'] is False
    assert value['rehearsal_qualified'] is True
    assert [r['milestones'] for r in value['snapshots']] == [
        {'first':'CURRENT','second':'CURRENT'}, {'first':'STALE','second':'CURRENT'},
        {'first':'FAILED','second':'CURRENT'}, {'first':'CURRENT','second':'CURRENT'}]
    assert value['controlled_outcomes'] == ['passed','passed','failed','passed']
    assert value['protected_inputs_unchanged']


@pytest.mark.parametrize('seconds', [True, float('nan'), float('inf'), 0, 241])
def test_invalid_budget_cannot_create_or_launch(tmp_path, seconds):
    from eval.input_scope_pilot import pilot
    with pytest.raises(ValueError):
        pilot(tmp_path/'new','python',ROOT,protocol='declared-runner',seconds=seconds,rehearse=True)
    assert not (tmp_path/'new').exists()


def test_receipts_without_native_runner_usage_do_not_qualify(tmp_path, monkeypatch):
    p=api()
    from core.config import Config, save
    from core.checks import execute
    from core.ledger import Ledger
    from core.hosts.provenance import fingerprint
    save(tmp_path,Config(auto_detect=False,commands={'tests':'echo 1 passed'}))
    (tmp_path/'source.py').write_text('value=1\n')
    Ledger(root=tmp_path,task='native-task').save()
    since=time.time(); execute(tmp_path,'tests')
    task=p.digest('native-task'); session='session'
    phases={name:{'processed':1,'session':p.digest(session),'task':task,'last_at':time.time()}
            for name in ('SessionStart','UserPromptSubmit','PostToolUse','Stop')}
    phases['SessionStart']['runtime_fingerprint']=fingerprint()
    monkeypatch.setattr(p,'diagnostics',lambda root:{'claude':{'phases':phases}})
    log=tmp_path/'native.jsonl'
    events=[{'type':'result','session_id':session,'is_error':False}]
    log.write_text('\n'.join(json.dumps(e) for e in events))
    assert p.observe(tmp_path,log,since=since,session=session,runtime=fingerprint())['native_runner_adoption'] is False
    events[:0]=[
        {'type':'assistant','session_id':session,'message':{'content':[{'type':'tool_use','id':'c','name':'Bash',
            'input':{'command':'python plugin/bin/ep_check.py tests --project .'}}]}},
        {'type':'user','session_id':session,'message':{'content':[{'type':'tool_result','tool_use_id':'c','content':'Declared check tests: passed'}]}}]
    log.write_text('\n'.join(json.dumps(e) for e in events))
    assert p.observe(tmp_path,log,since=since,session=session,runtime=fingerprint())['native_runner_adoption'] is True
    phases['Stop']['session']=p.digest('wrong')
    assert p.observe(tmp_path,log,since=since,session=session,runtime=fingerprint())['native_runner_adoption'] is False


def test_old_receipt_and_unfinished_call_do_not_establish_adoption(tmp_path, monkeypatch):
    p=api()
    log=tmp_path/'native.jsonl'
    log.write_text(json.dumps({'type':'assistant','message':{'content':[{'type':'tool_use','id':'c','name':'Bash',
        'input':{'command':'python ep_check.py tests'}}]}}))
    assert not p.observe(tmp_path,log,since=time.time(),session='s',runtime='a'*64)['native_runner_adoption']


def test_reserved_allowance_rejects_exhaustion_and_preserves_later_turns():
    p=api()
    assert [p.allowance(720,spent,4-index) for index,spent in enumerate((0,90,180,270))]==[180,210,270,450]
    assert p.allowance(240,240,1)==0
    with pytest.raises(ValueError): p.allowance(240,0,0)
