"""Behavioral controls for shared native diagnostics and fresh project health."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from core.config import Config, save
from core.evidence import Evidence, Kind, Result
from core.hosts.readiness import activation, callback, ingress
from core.hosts.setup import install
from core.ledger import Ledger

SOURCE = Path(__file__).resolve().parents[1]


def prepared(root, host='codex'):
    (root / 'app.py').write_text('answer = 1\n')
    for args in [('init', '-q'), ('add', 'app.py'),
                 ('-c', 'user.email=test@example.invalid', '-c', 'user.name=Test', 'commit', '-qm', 'base')]:
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
    save(root, Config(profile='off', commands={'tests': 'python -m pytest'}, strength={'enabled': False}))
    install(host, root, sys.executable, SOURCE)
    ledger = Ledger(root=root, task='task-one')
    ledger.save()
    return ledger


def test_native_phase_timing_is_bounded_and_private(tmp_path):
    prepared(tmp_path)
    for _ in range(35):
        with ingress('host'), callback('codex', tmp_path, 'SessionStart', {'session_id': 'private-session'}):
            pass
    data = activation('codex', tmp_path)
    phase = data['phases']['SessionStart']
    assert phase['processed'] == 35
    assert len(phase['samples_ms']) == 32
    assert all(x >= 0 for x in phase['samples_ms'])
    assert phase['session'] == hashlib.sha256(b'private-session').hexdigest()
    assert 'private-session' not in (tmp_path / '.elevenpowers/integrations.json').read_text()
    assert 'Stop' not in data['phases']


def test_replay_has_no_phase_samples_or_receipt_links(tmp_path):
    prepared(tmp_path)
    from core.hosts.readiness import record_receipts
    with ingress('replay'), callback('codex', tmp_path, 'PostToolUse'):
        record_receipts([Evidence(Kind.SUITE, 'private-node', Result.PASS, [], '', at=1)], 'task-one')
    data = activation('codex', tmp_path)
    assert not data.get('phases') and not data.get('receipt_links')


def test_receipt_links_cap_and_processing_error_are_explicit(tmp_path):
    prepared(tmp_path)
    from core.hosts.readiness import record_receipts
    for at in range(70):
        with ingress('host'), callback('codex', tmp_path, 'PostToolUse', {'session_id': 's'}):
            record_receipts([Evidence(Kind.SUITE, 'private-test-node', Result.FAIL, [], '', at=at, declaration='tests')], 'task-one')
    with ingress('host'), pytest.raises(OSError), callback('codex', tmp_path, 'Stop'):
        raise OSError('private-error-detail')
    data = activation('codex', tmp_path)
    assert len(data['receipt_links']) == 64 and data['links_evicted'] == 6
    assert data['phases']['Stop']['errors'] == 1
    assert data['phases']['Stop'].get('processed', 0) == 0
    assert 'private-test-node' not in json.dumps(data)
    assert 'private-error-detail' not in json.dumps(data)


def test_repaired_configuration_resets_phase_history(tmp_path):
    prepared(tmp_path)
    with ingress('host'), callback('codex', tmp_path, 'SessionStart'):
        pass
    path = tmp_path / '.codex/hooks.json'
    value = json.loads(path.read_text())
    value['hooks']['Stop'] = []
    path.write_text(json.dumps(value))
    install('codex', tmp_path, sys.executable, SOURCE)
    assert not activation('codex', tmp_path).get('phases')


def test_dispatch_links_only_successfully_saved_command_receipts(tmp_path):
    from core.hook import dispatch
    from core.hosts.readiness import receipt_key
    prepared(tmp_path)
    payload = {'cwd': str(tmp_path), '_ep_platform': 'codex', 'session_id': 's',
               'tool_name': 'Bash', 'tool_input': {'command': 'python -m pytest'},
               'tool_response': {'stdout': '1 passed in 0.1s', 'exit_code': 0}}
    with ingress('host'):
        dispatch('PostToolUse', payload)
        dispatch('Stop', {'cwd': str(tmp_path), '_ep_platform': 'codex', 'session_id': 's'})
    links = activation('codex', tmp_path)['receipt_links']
    saved = Ledger.load(tmp_path).evidence[-1]
    assert links[-1]['key'] == receipt_key(saved)
    assert links[-1]['result'] == 'pass' and links[-1]['execution'] == 'complete'
    assert activation('codex', tmp_path)['phases']['Stop']['task'] == hashlib.sha256(b'task-one').hexdigest()


def captured(root, status=0, host='codex', session='s'):
    from core.hook import dispatch
    payload = {'cwd': str(root), '_ep_platform': host, 'session_id': session}
    with ingress('host'):
        dispatch('SessionStart', payload.copy())
        dispatch('PostToolUse', {**payload, 'tool_name': 'Edit', 'tool_input': {'file_path': str(root / 'app.py')}})
        response = {'stdout': '1 passed in 0.1s' if status == 0 else '1 failed in 0.1s'}
        if status is not None:
            response['exit_code'] = status
        else:
            response['interrupted'] = True
        dispatch('PostToolUse', {**payload, 'tool_name': 'Bash', 'tool_input': {'command': 'python -m pytest'},
                                  'tool_response': response})
        dispatch('Stop', payload.copy())


def test_health_checks_freshness_once_and_does_not_write_or_run_tests(tmp_path, monkeypatch):
    from core.health import inspect
    from core import evidence, process
    prepared(tmp_path)
    captured(tmp_path)
    before = {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    calls = []
    real = evidence.source_snapshot
    def snapshot(*a, **kw):
        calls.append(1)
        return real(*a, **kw)
    monkeypatch.setattr(evidence, 'source_snapshot', snapshot)
    monkeypatch.setattr(process, 'run', lambda *a, **kw: pytest.fail('health executed a test/engine'))
    value = inspect('codex', tmp_path)
    assert value['health']['state'] == 'observed'
    assert value['latest_receipt']['freshness'] == 'fresh'
    assert value['task_state'] == 'UNVERIFIED'  # Pipeline health is not task certification.
    assert len(calls) == 1
    assert before == {str(p): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    (tmp_path / 'app.py').write_text('answer = 2\n')
    assert inspect('codex', tmp_path)['latest_receipt']['freshness'] == 'stale'


@pytest.mark.parametrize('status,expected', [(1, 'failed'), (None, 'incomplete')])
def test_capture_and_project_verification_are_separate(tmp_path, status, expected):
    from core.health import inspect
    prepared(tmp_path)
    captured(tmp_path, status)
    value = inspect('codex', tmp_path)
    assert value['health']['stages']['command_capture']['state'] == 'observed'
    assert value['health']['stages']['verification']['state'] == expected
    assert value['health']['state'] != 'observed'


def test_old_task_and_old_session_do_not_establish_completion(tmp_path):
    from core.health import inspect
    from core.hook import dispatch
    prepared(tmp_path)
    captured(tmp_path)
    ledger = Ledger.load(tmp_path)
    ledger.task = 'task-two'
    ledger.save()
    assert inspect('codex', tmp_path)['health']['stages']['completion']['state'] == 'waiting'
    with ingress('host'):
        dispatch('SessionStart', {'cwd': str(tmp_path), '_ep_platform': 'codex', 'session_id': 'new-session'})
    assert inspect('codex', tmp_path)['health']['stages']['command_capture']['state'] == 'waiting'


def test_health_reports_corrupt_and_budget_limited_state(tmp_path):
    from core.health import inspect
    prepared(tmp_path)
    (tmp_path / '.elevenpowers/integrations.json').write_text('{bad')
    value = inspect('codex', tmp_path)
    assert value['health']['state'] == 'incomplete'
    assert any('diagnostic' in x.lower() for x in value['next_actions'])
    value = inspect('codex', tmp_path, timeout=0)
    assert not value['coverage']['complete']
    assert value['health']['state'] == 'incomplete'


@pytest.mark.parametrize('seconds', [True, -1, float('nan'), float('inf'), 121])
def test_health_rejects_invalid_budget(tmp_path, seconds):
    from core.health import inspect
    prepared(tmp_path)
    with pytest.raises(ValueError, match='seconds'):
        inspect('codex', tmp_path, timeout=seconds)


def test_later_task_command_does_not_inherit_earlier_edit(tmp_path):
    from core.health import inspect
    from core.hook import dispatch
    prepared(tmp_path)
    captured(tmp_path)
    ledger = Ledger.load(tmp_path)
    ledger.task, ledger.evidence = 'new-task', []
    ledger.save()
    with ingress('host'):
        dispatch('PostToolUse', {'cwd': str(tmp_path), '_ep_platform': 'codex', 'session_id': 's',
                 'tool_name': 'Bash', 'tool_input': {'command': 'python -m pytest'},
                 'tool_response': {'stdout': '1 passed in 0.1s', 'exit_code': 0}})
        dispatch('Stop', {'cwd': str(tmp_path), '_ep_platform': 'codex', 'session_id': 's'})
    assert inspect('codex', tmp_path)['health']['stages']['edits']['state'] == 'waiting'


def test_all_declared_checks_required_even_if_latest_command_passed(tmp_path):
    from core.health import inspect
    from core.hook import dispatch
    prepared(tmp_path)
    save(tmp_path, Config(profile='off', commands={'tests': 'python -m pytest', 'build': 'python build.py'}, strength={'enabled': False}))
    captured(tmp_path)
    assert inspect('codex', tmp_path)['health']['stages']['verification']['state'] == 'waiting'
    with ingress('host'):
        dispatch('PostToolUse', {'cwd': str(tmp_path), '_ep_platform': 'codex', 'session_id': 's',
                 'tool_name': 'Bash', 'tool_input': {'command': 'python build.py'},
                 'tool_response': {'stdout': 'build failed', 'exit_code': 1}})
    captured(tmp_path)
    assert inspect('codex', tmp_path)['health']['stages']['verification']['state'] == 'failed'


@pytest.mark.parametrize('bad', [{'phases': {'Stop': []}}, {'phases': {'Stop': {'samples_ms': [float('inf')]}}},
                                  {'receipt_links': 'wrong-container'}])
def test_malformed_phase_metadata_is_actionable(tmp_path, bad):
    from core.health import inspect
    prepared(tmp_path)
    value = activation('codex', tmp_path)
    value.update(bad)
    (tmp_path / '.elevenpowers/integrations.json').write_text(json.dumps({'codex': value}))
    assert inspect('codex', tmp_path)['health']['state'] == 'incomplete'


def test_linked_saved_state_is_refused_without_following_it(tmp_path):
    from core.health import inspect
    prepared(tmp_path)
    path = tmp_path / '.elevenpowers/integrations.json'
    target = tmp_path / 'other.json'
    path.rename(target)
    try:
        path.symlink_to(target)
    except OSError:
        target.rename(path)
        pytest.skip('symlink privilege unavailable')
    assert inspect('codex', tmp_path)['health']['state'] == 'incomplete'
