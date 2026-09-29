"""Durable verification progress and ownership, independent of the host process."""
import json
import os
import signal
import subprocess
import sys
import time

import pytest

from core.jobs import Budget, BudgetExhausted, Busy, Session, read


def test_budget_is_shared_and_never_gives_more_than_remaining(monkeypatch):
    import core.jobs as jobs
    now = [10.0]
    monkeypatch.setattr(jobs.time, 'monotonic', lambda: now[0])
    budget = Budget(5)
    assert budget.timeout(300) == 5
    now[0] += 4
    assert budget.timeout(300) == 1
    now[0] += 2
    with pytest.raises(BudgetExhausted): budget.timeout(300)


def test_progress_is_durable_and_another_owner_cannot_run(tmp_path):
    with Session(tmp_path, 'task') as session:
        check = session.queue('tests', 'npm run ci')
        session.begin(check)
        assert read(tmp_path)['checks'][-1]['status'] == 'running'
        with pytest.raises(Busy):
            with Session(tmp_path, 'task'): pass
        session.finish(check, 'pass')
        assert read(tmp_path)['checks'][-1]['status'] == 'pass'
    with Session(tmp_path, 'task'):
        assert read(tmp_path)['checks'][-1]['status'] == 'pass'


def test_next_owner_marks_abandoned_run_incomplete(tmp_path):
    state = tmp_path / '.elevenpowers'
    state.mkdir()
    (state / 'verification.json').write_text(json.dumps({'task':'task','status':'running',
        'checks':[{'id':'old','phase':'tests','command':'checks','status':'running'}]}))
    with Session(tmp_path, 'task'):
        item = read(tmp_path)['checks'][0]
        assert item['status'] == 'incomplete'
        assert 'interrupted' in item['reason']


def test_queued_checks_are_deferred_when_session_exits(tmp_path):
    with Session(tmp_path, 'task') as session:
        session.queue('build', 'builder')
    assert read(tmp_path)['checks'][0]['status'] == 'deferred'


def test_journal_scrubs_secrets_and_ignores_itself(tmp_path):
    secret = 'ghp_' + 'PROBEONLY1234567890abcdefghijkl'
    with Session(tmp_path, 'task') as session:
        item = session.queue('tests', 'check --token=' + secret)
        session.finish(item, 'incomplete', secret)
    text = (tmp_path / '.elevenpowers/verification.json').read_text()
    assert secret not in text
    assert (tmp_path / '.elevenpowers/.gitignore').read_text().strip() == '*'


def test_new_task_does_not_inherit_old_queue(tmp_path):
    with Session(tmp_path, 'old') as session: session.queue('tests','old-command')
    with Session(tmp_path, 'new'):
        assert read(tmp_path)['checks'] == []

def test_killed_owner_releases_lock_and_keeps_completed_checks(tmp_path):
    code = ('from pathlib import Path; from core.jobs import Session; import sys,time; '
            's=Session(Path(sys.argv[1]),"task"); s.__enter__(); '
            'a=s.queue("tests","first"); s.finish(a,"pass"); '
            'b=s.queue("build","second"); s.begin(b); '
            'print(__import__("os").getpid(),flush=True); time.sleep(60)')
    child = subprocess.Popen([sys.executable, '-c', code, str(tmp_path)], stdout=subprocess.PIPE, text=True)
    try:
        owner_pid = int(child.stdout.readline().strip())
        with pytest.raises(Busy):
            with Session(tmp_path, 'task'): pass
    finally:
        os.kill(owner_pid, signal.SIGTERM)
        child.wait(timeout=10)
        child.stdout.close()
    with Session(tmp_path, 'task'):
        assert [c['status'] for c in read(tmp_path)['checks']] == ['pass','incomplete']
