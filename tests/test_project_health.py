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

