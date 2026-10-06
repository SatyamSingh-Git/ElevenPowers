import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from core.evidence import Kind, Result, tree_hash
from core.ledger import Ledger
from test_milestone_history import project, receipt

CLI = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_milestones.py'


def saved(root, **kwargs):
    project(root)
    ledger = Ledger(root=root, task='first')
    ledger.add([receipt(root, **kwargs)]); ledger.save()
    return ledger


def test_current_evidence_survives_a_new_task_and_read_is_pure(tmp_path, monkeypatch):
    from core.milestones import build
    ledger = saved(tmp_path)
    Ledger(root=tmp_path, task='second').save()
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    original = subprocess.run
    def metadata_only(args, *a, **k):
        assert args[0] == 'git'
        assert any(word in args for word in ('rev-parse', 'ls-files', 'check-ignore'))
        assert 'core.fsmonitor=false' in args
        return original(args, *a, **k)
    monkeypatch.setattr(subprocess, 'run', metadata_only)
    value = build(tmp_path)
    assert value['state'] == 'CURRENT' and value['milestones'][0]['state'] == 'CURRENT'
    assert value['milestones'][0]['checks'][0]['recorded_at'] == ledger.evidence[0].at
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    assert before == after


@pytest.mark.parametrize('kwargs,state', [
    ({'result': Result.FAIL}, 'FAILED'),
    ({'result': Result.ERROR, 'execution': 'incomplete'}, 'INCOMPLETE'),
])
def test_failed_and_incomplete_execution_are_distinct(tmp_path, kwargs, state):
    from core.milestones import build
    saved(tmp_path, **kwargs)
    value = build(tmp_path)
    assert value['milestones'][0]['state'] == state
    assert value['milestones'][0]['checks'][0]['result'] == kwargs['result'].value


def test_missing_and_wrong_command_evidence_cannot_qualify(tmp_path):
    from core.milestones import build
    project(tmp_path)
    assert build(tmp_path)['state'] == 'ABSENT'
    saved(tmp_path, command='python -m pytest tests/test_other.py')
    assert build(tmp_path)['state'] == 'ABSENT'


@pytest.mark.parametrize('target', ['provider.py', 'elevenpowers.milestones.json', 'requirements.txt'])
def test_source_expectation_and_dependency_edits_expire_old_evidence(tmp_path, target):
    from core.milestones import build
    project(tmp_path)
    (tmp_path / 'requirements.txt').write_text('example==1\n')
    ledger = Ledger(root=tmp_path, task='first'); ledger.add([receipt(tmp_path)]); ledger.save()
    assert build(tmp_path)['state'] == 'CURRENT'
    path = tmp_path / target
    stamp = path.stat()
    if target.endswith('.json'):
        value = json.loads(path.read_text()); value['milestones'][0]['description'] = 'A changed expectation.'
        path.write_text(json.dumps(value))
    else:
        path.write_text('value = 2\n')
    os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    assert build(tmp_path)['state'] == 'STALE'


@pytest.mark.parametrize('fault', ['empty', 'missing_manifest', 'wrong_inventory', 'zero_tests', 'contradictory_counts'])
def test_scope_and_count_gaps_are_not_current(tmp_path, fault):
    from core.milestones import build
    project(tmp_path)
    item = receipt(tmp_path)
    if fault == 'empty':
        item.scope = ''; item.observed = []; item.tree = 'empty'
    elif fault == 'missing_manifest':
        item.scope = ''; item.observed = ['provider.py', 'tests/test_login.py']
        item.tree = tree_hash(tmp_path, item.observed)
    elif fault == 'wrong_inventory':
        item.observed.append('invented.py')
    elif fault == 'zero_tests':
        item.passed = 0
    else:
        item.failed = 1
    ledger = Ledger(root=tmp_path, task='first'); ledger.add([item]); ledger.save()
    assert build(tmp_path)['state'] == 'INCOMPLETE'


def test_changed_command_declaration_is_stale(tmp_path):
    from core.milestones import build
    project(tmp_path)
    state = tmp_path / '.elevenpowers'; state.mkdir()
    config = state / 'config.json'
    config.write_text(json.dumps({'auto_detect': False, 'commands': {'tests': 'python -m pytest tests/test_login.py'}}))
    item = receipt(tmp_path); item.declaration = 'tests'; item.declared_command = item.command
    ledger = Ledger(root=tmp_path, task='first'); ledger.add([item]); ledger.save()
    assert build(tmp_path)['state'] == 'CURRENT'
    config.write_text(json.dumps({'auto_detect': False, 'commands': {'tests': 'python -m pytest tests/test_new.py'}}))
    assert build(tmp_path)['state'] == 'STALE'


def test_explicit_scope_does_not_expire_for_an_unrelated_input(tmp_path):
    from core.milestones import build
    project(tmp_path)
    (tmp_path / 'unrelated.py').write_text('value = 1')
    item = receipt(tmp_path); item.scope = ''
    item.observed = ['provider.py', 'tests/test_login.py', 'elevenpowers.milestones.json']
    item.tree = tree_hash(tmp_path, item.observed)
    ledger = Ledger(root=tmp_path, task='first'); ledger.add([item]); ledger.save()
    (tmp_path / 'unrelated.py').write_text('value = 2')
    assert build(tmp_path)['state'] == 'CURRENT'


def test_deleted_declared_input_and_exhausted_budget_remain_visible(tmp_path):
    from core.milestones import build
    saved(tmp_path)
    (tmp_path / 'provider.py').unlink()
    value = build(tmp_path)
    assert value['state'] == 'INCOMPLETE'
    assert any('provider.py' in issue for issue in value['coverage']['issues'])
    assert build(tmp_path, seconds=0)['state'] == 'INCOMPLETE'


def test_corrupt_or_oversized_ledger_does_not_look_like_clean_absence(tmp_path):
    from core.milestones import build
    ledger = saved(tmp_path)
    ledger.path.write_text('{broken')
    assert build(tmp_path)['state'] == 'INCOMPLETE'
    ledger.path.write_bytes(b' ' * (8 * 1024 * 1024 + 1))
    assert build(tmp_path)['state'] == 'INCOMPLETE'


def test_detected_state_movement_makes_the_report_incomplete(tmp_path, monkeypatch):
    from core.milestones import report
    ledger = saved(tmp_path)
    original = report.read_ledger
    calls = []
    def moving(root, deadline):
        value = original(root, deadline)
        calls.append(1)
        if len(calls) == 1:
            raw = json.loads(ledger.path.read_text()); raw['task'] = 'changed during collection'
            ledger.path.write_text(json.dumps(raw))
        return value
    monkeypatch.setattr(report, 'read_ledger', moving)
    value = report.build(tmp_path)
    assert value['state'] == 'INCOMPLETE'
    assert any('changed' in issue for issue in value['coverage']['issues'])


def test_redacted_exact_command_cannot_be_certified(tmp_path):
    from core.milestones import build
    project(tmp_path)
    token = 'ghp_' + 'A' * 30
    value = json.loads((tmp_path / 'elevenpowers.milestones.json').read_text())
    value['milestones'][0]['checks'][0]['command'] += f' --token={token}'
    (tmp_path / 'elevenpowers.milestones.json').write_text(json.dumps(value))
    result = build(tmp_path)
    assert result['state'] == 'INCOMPLETE'
    assert token not in json.dumps(result)


def test_json_markdown_and_portable_report_preserve_separate_task_state(tmp_path):
    from core.milestones import build, markdown
    from core.export import build as export
    saved(tmp_path)
    value = build(tmp_path)
    text = markdown(value)
    assert 'CURRENT' in text and 'login' in text
    assert 'private output' not in text and str(tmp_path) not in text
    exported = export(tmp_path)
    assert exported['milestones']['state'] == 'CURRENT'
    assert exported['state'] == 'UNVERIFIED'  # No active task claim.


def test_cli_gate_and_atomic_output(tmp_path):
    root = tmp_path / 'project'; root.mkdir(); saved(root)
    args = [sys.executable, str(CLI), '--project', str(root), '--json', '--check']
    done = subprocess.run(args, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout)['state'] == 'CURRENT'
    output = tmp_path / 'report.json'
    done = subprocess.run(args + ['--output', str(output)], capture_output=True, text=True)
    assert done.returncode == 0
    before = output.read_bytes()
    done = subprocess.run(args + ['--output', str(output)], capture_output=True, text=True)
    assert done.returncode != 0 and output.read_bytes() == before
    (root / 'provider.py').write_text('value = 2')
    assert subprocess.run(args, capture_output=True).returncode == 1
