import json
from core.jobs import Session
from core.ledger import Ledger
from core.status import render
from core.report import end_report


def test_progress_is_visible_while_running(tmp_path):
    ledger = Ledger(root=tmp_path, task='task')
    ledger.save()
    with Session(tmp_path, 'task') as session:
        check = session.queue('verification', 'check-the-project')
        session.begin(check)
        for output in (render(tmp_path), end_report(ledger)):
            assert 'running' in output
            assert 'check-the-project' in output


def test_abandoned_owner_is_reported_without_rewriting_state(tmp_path):
    ledger = Ledger(root=tmp_path, task='task')
    ledger.save()
    path = tmp_path/'.elevenpowers/verification.json'
    payload = json.dumps({'task':'task','id':'x','status':'running', 'checks':[
        {'run':'x','phase':'verification','command':'check-the-project','status':'running'}]})
    path.write_text(payload)
    output = render(tmp_path)
    assert 'interrupted' in output
    assert 'next completion' in output
    assert path.read_text() == payload


def test_history_and_deferred_work_are_distinguished(tmp_path):
    ledger = Ledger(root=tmp_path, task='task')
    ledger.save()
    with Session(tmp_path, 'task') as session:
        item = session.queue('verification', 'first-check')
        session.finish(item, 'passed')
        session.queue('verification','later-check')
    output = render(tmp_path)
    assert 'deferred' in output and 'later-check' in output
    assert 'passed' in output and 'first-check' in output


def test_new_task_ignores_previous_progress(tmp_path):
    with Session(tmp_path, 'old') as session:
        session.queue('verification', 'old-command')
    Ledger(root=tmp_path, task='new').save()
    assert 'old-command' not in render(tmp_path)


def test_completion_report_does_not_claim_finished_checks_are_running(tmp_path):
    ledger = Ledger(root=tmp_path, task='task')
    ledger.save()
    with Session(tmp_path, 'task') as session:
        item = session.queue('verification', 'done-command')
        session.finish(item, 'passed')
        assert 'checks recorded; completion finishing' in end_report(ledger)
