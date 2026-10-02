"""Real frozen files/grading; only subscription host invocation is replaced."""
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from core import health
from eval import benefit, challenge, proposals, subscription


def _native(monkeypatch):
    monkeypatch.setattr(health,'inspect',lambda *a,**k:{'health':{'state':'observed'}})
    monkeypatch.setattr(subscription,'auth',lambda *a:True)


def test_successful_stop_then_failed_record_remains_incomplete(tmp_path,monkeypatch):
    root=tmp_path/'candidate';root.mkdir();(root/'app.py').write_bytes(b'candidate')
    manifest=tmp_path/'contract.json'
    config={'root':str(root),'files':['app.py'],'host':'claude','plugin':[],
            'history':str(tmp_path/'history.jsonl'),'attempts':str(tmp_path/'attempts')}
    manifest.write_text(json.dumps(config))
    def invoke():
        monkeypatch.setattr(proposals.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(json.dumps({'cwd':str(root)}).encode())))
        return proposals.hook(manifest,'Stop')
    assert invoke()==0
    assert len(proposals.read(config['history']))==1
    def fail(*a,**k):raise OSError('sink unavailable')
    monkeypatch.setattr(proposals,'append',fail)
    assert invoke()==0
    with pytest.raises(ValueError,match='observation'):
        proposals.observed(config)


def test_prepared_configuration_drift_is_retained_before_auth(tmp_path,monkeypatch):
    root=tmp_path/'batch';benefit.prepare_batch(root)
    (root/'atomic-repair-1-tool/.claude/settings.local.json').write_text('{}')
    _native(monkeypatch)
    with pytest.raises(ValueError,match='prepared'):
        benefit.run_batch(root,'unused',root)
    assert json.loads((root/'attempt.json').read_text())['state']=='setup_failed'


def test_new_project_settings_change_the_configuration_seal(tmp_path):
    root=tmp_path/'batch';benefit.prepare_batch(root)
    candidate=root/'atomic-repair-0-tool'
    before=benefit._seal(root,candidate)
    (candidate/'.claude/settings.json').write_text('{"permissions":{}}')
    assert benefit._seal(root,candidate)!=before


def test_evaluator_entry_point_is_bound_to_harness(tmp_path,monkeypatch):
    directory=Path(challenge.__file__).parent
    copy=tmp_path/'challenge.py';copy.write_bytes(Path(challenge.__file__).read_bytes())
    monkeypatch.setattr(challenge,'__file__',str(copy))
    before=benefit._harness()
    copy.write_bytes(copy.read_bytes()+b'\n# changed grading orchestration\n')
    assert benefit._harness()!=before


@pytest.mark.parametrize('outcome',['false','error','timeout'])
def test_authentication_failure_is_durable_and_cannot_be_retried(tmp_path,monkeypatch,outcome):
    import subprocess
    root=tmp_path/'batch';benefit.prepare_batch(root);_native(monkeypatch)
    def auth(*a):
        if outcome=='error':raise ValueError('API environment refused')
        if outcome=='timeout':raise subprocess.TimeoutExpired('auth',10)
        return False
    monkeypatch.setattr(subscription,'auth',auth)
    with pytest.raises(ValueError):benefit.run_batch(root,'unused',root)
    attempt=json.loads((root/'attempt.json').read_text())
    assert attempt['state']=='setup_failed' and attempt['phase']=='subscription_auth'
    with pytest.raises(ValueError,match='attempted'):benefit.run_batch(root,'unused',root)


def test_unreadable_candidate_seal_does_not_erase_attempt(tmp_path,monkeypatch):
    root=tmp_path/'batch';benefit.prepare_batch(root);_native(monkeypatch)
    (root/'atomic-repair-0-baseline/.claude/settings.local.json').unlink()
    with pytest.raises(ValueError):benefit.run_batch(root,'unused',root)
    assert json.loads((root/'attempt.json').read_text())['state']=='setup_failed'
