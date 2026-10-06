import json
import time

import pytest

from core.evidence import Evidence, Kind, Result, source_snapshot
from core.ledger import Ledger
from test_milestone_definition import declaration


def project(root):
    declaration(root)
    (root / 'provider.py').write_text('value = 1\n')
    (root / 'tests').mkdir(exist_ok=True)
    (root / 'tests/test_login.py').write_text('def test_login():\n    assert True\n')
    return root


def receipt(root, *, command='python -m pytest tests/test_login.py', result=Result.PASS,
            execution='complete', at=None):
    scan, tree = source_snapshot(root, fresh=True)
    return Evidence(kind=Kind.SUITE, identity='suite', command=command, result=result,
                    execution=execution, observed=scan.files, tree=tree, scope='source',
                    counted=True, passed=1 if result is Result.PASS else 0,
                    failed=1 if result is Result.FAIL else 0, at=at or time.time(),
                    detail='private output must not enter milestone history')


def test_new_task_keeps_history_without_adopting_claim_evidence(tmp_path):
    root = project(tmp_path)
    first = Ledger(root=root, task='first', request='private request')
    first.add([receipt(root)]); first.save()
    Ledger(root=root, task='second').save()
    second = Ledger.load(root)
    assert second.evidence == [] and second.claims == []
    saved = second.milestone_history['receipts']
    assert len(saved) == 1 and saved[0]['detail'] == ''
    assert 'private' not in json.dumps(second.milestone_history)


def test_latest_incomplete_attempt_survives_task_transition(tmp_path):
    root = project(tmp_path)
    first = Ledger(root=root, task='first')
    first.add([receipt(root, at=10)]); first.save()
    first.add([receipt(root, result=Result.ERROR, execution='incomplete', at=11)])
    first.save()
    Ledger(root=root, task='second').save()
    saved = Ledger.load(root).milestone_history['receipts']
    assert len(saved) == 1 and saved[0]['execution'] == 'incomplete'


def test_stale_writer_cannot_overwrite_latest_history_observation(tmp_path):
    root = project(tmp_path)
    old = Ledger(root=root, task='first')
    old.add([receipt(root, at=10)]); old.save()
    new = Ledger(root=root, task='second')
    new.add([receipt(root, result=Result.FAIL, at=12)]); new.save()
    old.save()
    saved = Ledger.load(root).milestone_history['receipts']
    assert len(saved) == 1 and saved[0]['result'] == 'fail'


def test_equal_timestamp_old_writer_replay_does_not_replace_later_failure(tmp_path):
    from core.milestones import build
    root = project(tmp_path)
    old = Ledger(root=root, task='first')
    old.add([receipt(root, at=10)]); old.save()
    new = Ledger(root=root, task='second')
    new.add([receipt(root, result=Result.FAIL, at=10)]); new.save()
    assert build(root)['state'] == 'FAILED'
    old.save()
    assert build(root)['state'] == 'FAILED'


def test_same_task_new_observation_wins_tie_but_save_replay_does_not(tmp_path):
    from core.milestones import build
    root = project(tmp_path)
    ledger = Ledger(root=root, task='first')
    ledger.add([receipt(root, at=10)]); ledger.save()
    ledger.add([receipt(root, result=Result.FAIL, at=10)]); ledger.save()
    assert build(root)['state'] == 'FAILED'
    Ledger.load(root).save()
    assert build(root)['state'] == 'FAILED'


def test_transient_invalid_declaration_recovers_after_valid_fresh_capture(tmp_path):
    from core.milestones import build
    root = project(tmp_path)
    path = root / 'elevenpowers.milestones.json'
    valid = path.read_bytes(); path.write_text('{')
    ledger = Ledger(root=root, task='first'); ledger.save()
    assert build(root)['state'] == 'INCOMPLETE'
    path.write_bytes(valid)
    ledger.add([receipt(root)]); ledger.save()
    assert build(root)['state'] == 'CURRENT'


def test_unknown_history_gap_recovers_only_after_all_checks_have_new_observations(tmp_path):
    from core.milestones import build
    root = project(tmp_path)
    value = declaration(root)
    worker_command = 'python -m pytest tests/test_worker.py'
    value['milestones'][0]['checks'].append({'kind': 'test_suite', 'command': worker_command})
    (root / 'elevenpowers.milestones.json').write_text(json.dumps(value))
    ledger = Ledger(root=root, task='first')
    ledger.add([receipt(root), receipt(root, command=worker_command)])
    ledger.save()
    raw = json.loads(ledger.path.read_text()); raw['milestone_history'] = {'schema': 99}
    ledger.path.write_text(json.dumps(raw))
    recovered = Ledger.load(root); recovered.save()
    assert build(root)['state'] == 'INCOMPLETE'
    recovered.add([receipt(root)]); recovered.save()
    assert build(root)['state'] == 'INCOMPLETE'
    recovered.add([receipt(root, command=worker_command)]); recovered.save()
    assert build(root)['state'] == 'CURRENT'


def test_removing_declaration_stops_new_receipt_capture(tmp_path):
    root = project(tmp_path)
    ledger = Ledger(root=root, task='first'); ledger.add([receipt(root, at=10)]); ledger.save()
    (root / 'elevenpowers.milestones.json').unlink()
    ledger.add([receipt(root, result=Result.FAIL, at=11)]); ledger.save()
    assert ledger.milestone_history['receipts'][0]['result'] == 'pass'


def test_malformed_prior_diagnostics_cannot_break_recovery(tmp_path):
    from core.milestones.history import retain
    root = project(tmp_path)
    for bad in (10, [[]], {'issue': 'invalid'}):
        value = retain(root, {'schema': 1, 'receipts': [], 'issues': bad}, [receipt(root)])
        assert value['issues']


def test_unconfigured_projects_do_not_gain_milestone_state(tmp_path):
    ledger = Ledger(root=tmp_path, task='ordinary')
    ledger.save()
    assert 'milestone_history' not in json.loads(ledger.path.read_text())


def test_wrong_command_and_nonaggregate_receipts_are_not_captured(tmp_path):
    root = project(tmp_path)
    ledger = Ledger(root=root, task='first')
    wrong = receipt(root, command='python -m pytest tests/test_other.py')
    individual = receipt(root); individual.kind = Kind.TEST
    ledger.add([wrong, individual]); ledger.save()
    assert Ledger.load(root).milestone_history['receipts'] == []


def test_history_budget_and_invalid_metadata_remain_explicit(tmp_path, monkeypatch):
    from core.milestones import history
    root = project(tmp_path)
    monkeypatch.setattr(history, 'MAX_BYTES', 20)
    value = history.retain(root, {}, [receipt(root)])
    assert value['issues'] and not value['receipts']
    monkeypatch.setattr(history, 'MAX_BYTES', 4 * 1024 * 1024)
    bad = receipt(root); bad.at = float('nan')
    value = history.retain(root, {}, [bad])
    assert value['issues'] and not value['receipts']


def test_unreadable_history_is_not_replaced_with_claim_of_completeness(tmp_path):
    from core.milestones.history import retain
    root = project(tmp_path)
    value = retain(root, {'schema': 2, 'receipts': []}, [receipt(root)])
    assert value['issues'] and len(value['receipts']) == 1


def test_latest_entry_wins_timestamp_tie_and_snapshot_is_not_rebound(tmp_path):
    root = project(tmp_path)
    first = receipt(root, at=10)
    second = receipt(root, at=10, result=Result.FAIL)
    ledger = Ledger(root=root, task='first')
    ledger.add([first, second]); ledger.save()
    stored = Ledger.load(root).milestone_history['receipts'][0]
    assert stored['result'] == 'fail' and stored['tree'] == second.tree
    (root / 'provider.py').write_text('value = 2\n')
    Ledger(root=root, task='next').save()
    assert Ledger.load(root).milestone_history['receipts'][0]['tree'] == second.tree


def test_record_limit_retains_newest_and_exposes_omitted_command(tmp_path, monkeypatch):
    from core.milestones import history
    root = project(tmp_path)
    value = declaration(root)
    value['milestones'][0]['checks'].append({'kind': 'test_suite', 'command': 'python -m pytest tests/test_worker.py'})
    (root / 'elevenpowers.milestones.json').write_text(json.dumps(value))
    monkeypatch.setattr(history, 'MAX_RECORDS', 1)
    result = history.retain(root, {}, [receipt(root, at=10),
                receipt(root, command='python -m pytest tests/test_worker.py', at=11)])
    assert len(result['receipts']) == 1 and result['receipts'][0]['at'] == 11
    assert result['issues']
