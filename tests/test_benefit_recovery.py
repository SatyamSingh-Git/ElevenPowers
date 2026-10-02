"""An interrupted controller may finish unstarted slots, never repeat an attempt."""
import json
from types import SimpleNamespace

import pytest

from core import health
from eval import benefit, hard_cases, subscription


def test_finish_unstarted_slots_preserves_an_interrupted_call(tmp_path,monkeypatch):
    root=tmp_path/'batch';benefit.prepare_batch(root,seconds=480,suite=hard_cases,repeats=1,model='claude-sonnet-5')
    monkeypatch.setattr(health,'inspect',lambda *a,**k:{'health':{'state':'observed'}})
    monkeypatch.setattr(subscription,'auth',lambda *a:True)
    calls=[];real=benefit.run
    def interrupted(args,**kwargs):
        if '--model' not in args:return real(args,**kwargs)
        calls.append(str(kwargs['cwd']))
        if len(calls)==2:raise KeyboardInterrupt('controller interruption')
        return SimpleNamespace(returncode=1,stdout='{}',stderr='')
    monkeypatch.setattr(benefit,'run',interrupted)
    with pytest.raises(KeyboardInterrupt):benefit.run_batch(root,'unused',root)
    monkeypatch.setattr(benefit,'_controller_running',lambda pid:False)
    with pytest.raises(ValueError,match='attempted'):benefit.run_batch(root,'unused',root)
    result=benefit.run_batch(root,'unused',root,finish_unstarted=True)
    assert len(calls)==8 and len(set(calls))==8
    assert result['state']=='inconclusive'
    record=json.loads((root/'lease-queue-0-tool-result.json').read_text())
    assert record['state']=='interrupted' and record['final_snapshot']['state']=='complete'
    assert json.loads((root/'attempt.json').read_text())['state']=='running'
    assert json.loads((root/'continuation.json').read_text())['state']=='finished'
    with pytest.raises(ValueError):benefit.run_batch(root,'unused',root,finish_unstarted=True)


def test_post_run_seal_covers_nested_instruction_files(tmp_path):
    root=tmp_path/'batch';benefit.prepare_batch(root)
    candidate=root/'atomic-repair-0-tool';before=benefit._configuration_seal(root,candidate)
    (candidate/'.claude/CLAUDE.md').write_text('ordinary new instruction')
    assert benefit._configuration_seal(root,candidate)!=before


def test_current_controller_cannot_be_replaced(tmp_path):
    import os
    root=tmp_path/'batch';benefit.prepare_batch(root,seconds=480,suite=hard_cases,repeats=1,model='claude-sonnet-5')
    assert benefit._controller_running(os.getpid())
    (root/'attempt.json').write_text(json.dumps({'state':'running','controller_pid':os.getpid()}))
    with pytest.raises(ValueError,match='active'):benefit.run_batch(root,'unused',root,finish_unstarted=True)
