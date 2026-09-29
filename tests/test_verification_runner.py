"""Verification owns execution state and saves evidence before the next check."""
import subprocess
from pathlib import Path

import pytest

from core import verify
from core.config import Config, save
from core.evidence import Freshness, Result
from core.jobs import Session, read
from core.ledger import Ledger


def configured(tmp_path, commands=None):
    save(tmp_path, Config(commands=commands or {'tests':'check-tests'}, auto_detect=False))
    (tmp_path / 'source.py').write_text('value = 1')
    return Ledger(root=tmp_path, task='runner-task')


def test_completed_receipt_saved_before_next_check(tmp_path, monkeypatch):
    ledger = configured(tmp_path, {'tests':'check-tests','build':'check-build'})
    monkeypatch.setattr(verify, 'dischargeable', lambda _: ['tests','build'])
    def run(command, **kwargs):
        if command == 'check-build':
            persisted = Ledger.load(tmp_path).evidence
            assert any(e.command=='check-tests' and e.result is Result.PASS for e in persisted)
            raise KeyboardInterrupt()
        return subprocess.CompletedProcess(command, 0, '# pass 1\n# fail 0', '')
    monkeypatch.setattr(verify, 'run_command', run)
    with pytest.raises(KeyboardInterrupt): verify.discharge(ledger)
    assert any(e.result is Result.PASS for e in Ledger.load(tmp_path).evidence)
    assert read(tmp_path)['checks'][-1]['status'] == 'incomplete'


def test_source_changed_during_success_cannot_be_fresh(tmp_path, monkeypatch):
    ledger = configured(tmp_path)
    monkeypatch.setattr(verify, 'dischargeable', lambda _: ['tests'])
    def run(command, **kwargs):
        (tmp_path/'source.py').write_text('value = 2')
        return subprocess.CompletedProcess(command, 0, '# pass 1\n# fail 0', '')
    monkeypatch.setattr(verify, 'run_command', run)
    receipt = verify.discharge(ledger)[0]
    assert receipt.freshness(tmp_path) is Freshness.STALE
    assert 'changed during' in ' '.join(receipt.coverage_issues)
    assert read(tmp_path)['checks'][-1]['status'] == 'stale'


def test_exhausted_budget_defers_without_launch(tmp_path, monkeypatch):
    ledger = configured(tmp_path)
    monkeypatch.setattr(verify, 'dischargeable', lambda _: ['tests'])
    monkeypatch.setattr(verify, 'run_command', lambda *a, **k: pytest.fail('launched after budget'))
    with Session(tmp_path, ledger.task, seconds=0):
        assert verify.discharge(ledger) == []
    assert read(tmp_path)['checks'][-1]['status'] == 'deferred'


def test_passive_discharge_does_no_work(tmp_path, monkeypatch):
    save(tmp_path, Config(profile='off', commands={'tests':'check-tests'}))
    monkeypatch.setattr(verify, 'run_command', lambda *a, **k: pytest.fail('passive execution'))
    assert verify.discharge(Ledger(root=tmp_path)) == []
    assert not (tmp_path/'.elevenpowers/verification.json').exists()


def test_fresh_success_is_reused_after_reload_and_edit_invalidates(tmp_path, monkeypatch):
    from core.obligations import Claim
    ledger = configured(tmp_path)
    ledger.claims = [Claim.BUG_FIXED]
    ledger.touched = ['source.py']
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, '# pass 1\n# fail 0', '')
    monkeypatch.setattr(verify, 'run_command', run)
    first = verify.discharge(ledger)
    assert first
    ledger.add(first)  # Compatibility callers do not duplicate durable receipts.
    assert sum(e.execution == 'complete' for e in ledger.evidence) == 1
    assert verify.discharge(Ledger.load(tmp_path)) == []
    assert len(calls) == 1
    (tmp_path/'source.py').write_text('value = 2')
    assert verify.discharge(Ledger.load(tmp_path))
    assert len(calls) == 2


def test_failure_after_success_is_saved_and_interrupt_marker_supersedes(tmp_path, monkeypatch):
    from core.obligations import Claim
    from core.ledger import Status
    ledger = configured(tmp_path)
    ledger.claims = [Claim.BUG_FIXED]
    monkeypatch.setattr(verify, 'dischargeable', lambda _: ['tests'])
    monkeypatch.setattr(verify, 'run_command', lambda command, **kw:
                        subprocess.CompletedProcess(command, 0, '# pass 1\n# fail 0', ''))
    verify.discharge(ledger)
    def interrupt(*a, **k):
        assert Ledger.load(tmp_path).evidence[-1].execution == 'incomplete'
        raise KeyboardInterrupt()
    monkeypatch.setattr(verify, 'run_command', interrupt)
    with pytest.raises(KeyboardInterrupt):
        verify.discharge(ledger)
    assert Ledger.load(tmp_path).status() is not Status.VERIFIED
    monkeypatch.setattr(verify, 'run_command', lambda command, **kw:
                        subprocess.CompletedProcess(command, 1, '# pass 0\n# fail 1', ''))
    verify.discharge(ledger)
    assert Ledger.load(tmp_path).evidence[-1].result is Result.FAIL
    assert read(tmp_path)['checks'][-1]['status'] == 'failed'


def test_rewrite_with_restored_metadata_is_detected(tmp_path, monkeypatch):
    import os
    import time
    ledger = configured(tmp_path)
    path = tmp_path/'source.py'
    old = time.time() - 100
    os.utime(path, (old, old))
    monkeypatch.setattr(verify, 'dischargeable', lambda _: ['tests'])
    def run(command, **kw):
        path.write_text('value = 2')
        os.utime(path, (old, old))
        return subprocess.CompletedProcess(command, 0, '# pass 1\n# fail 0', '')
    monkeypatch.setattr(verify, 'run_command', run)
    assert verify.discharge(ledger)[0].coverage_issues


def test_expired_snapshot_is_explicitly_incomplete(tmp_path):
    from core.evidence import source_snapshot
    scan, digest = source_snapshot(tmp_path, deadline=0)
    assert not scan.complete
    assert 'deadline' in scan.issues[0]
