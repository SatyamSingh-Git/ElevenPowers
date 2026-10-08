"""Synthetic launcher/callback controls, never installed-session acceptance."""
from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
import sys

import pytest

from core.hosts import readiness
from core.hosts.setup import install
from core.milestones.automatic import deliver
from test_milestone_advice_worker import opted

SOURCE = Path(__file__).resolve().parents[1]
EVENTS = {'claude': 'PostToolUse', 'codex': 'PostToolUse', 'gemini': 'AfterTool',
          'cursor': 'postToolUse', 'copilot': 'postToolUse'}


def project(root, host='claude'):
    ledger = opted(root)
    install(host, root, sys.executable, SOURCE)
    return ledger


def attempts(root):
    return json.loads((root / '.elevenpowers/advice.json').read_text())['tasks'][0]['attempts']


@contextmanager
def native_advice(root):
    from core.milestones import delivery
    ledger = project(root)
    with readiness.ingress('host'), delivery.collect():
        with readiness.callback('claude', root, 'PostToolUse', {'session_id': 'private-session'}):
            context = deliver(ledger)
        yield context


def test_worker_context_is_generated_without_claiming_emission(tmp_path):
    ledger = project(tmp_path)
    assert 'milestone advice' in deliver(ledger)
    row = attempts(tmp_path)[0]
    assert row['status'] == 'delivered'  # Legacy means the worker returned text.
    assert len(row['checks']) == 2
    assert 'emission' not in row
    assert 'command' not in json.dumps(row)


@pytest.mark.parametrize('host', EVENTS)
@pytest.mark.parametrize('replay', [False, True])
def test_actual_launcher_flush_records_native_context_only(tmp_path, host, replay):
    project(tmp_path, host)
    payload = {'cwd': str(tmp_path), 'session_id': 'private-session', 'tool_name': 'Write',
               'tool_input': {'file_path': str(tmp_path / 'cli.py')},
               'tool_response': {'exit_code': 0}}
    if host == 'gemini':
        payload['tool_name'] = 'write_file'
    if host == 'copilot':
        payload.update(toolName='create', toolArgs=payload['tool_input'], sessionId='private-session')
    args = ([sys.executable, str(SOURCE / 'plugin/bin/ep_hook.py'), EVENTS[host]] if host == 'claude'
            else [sys.executable, str(SOURCE / 'plugin/bin/ep_host.py'), host, EVENTS[host]])
    if replay:
        args.append('--replay')
    done = subprocess.run(args, input=json.dumps(payload), capture_output=True,
                          text=True, timeout=25, cwd=SOURCE)
    assert done.returncode == 0, done.stderr
    assert 'milestone advice' in json.dumps(json.loads(done.stdout))
    row = attempts(tmp_path)[0]
    if replay:
        assert 'emission' not in row
    else:
        emission = row['emission']
        assert emission['host'] == host
        assert emission['session'] == readiness.identity('private-session')
        assert emission['generation'] == readiness.activation(host, tmp_path)['generation']
        assert len(emission['runtime']) == len(emission['context']) == 64
        assert emission['at'] >= row['at']
    assert 'private-session' not in (tmp_path / '.elevenpowers/advice.json').read_text()


@pytest.mark.parametrize('field', ['systemMessage', 'reason', 'error'])
def test_non_context_fields_cannot_claim_emission(tmp_path, field):
    from core.milestones import delivery
    with native_advice(tmp_path) as context:
        delivery.emitted({field: context})
    assert 'emission' not in attempts(tmp_path)[0]


def test_partial_context_cannot_claim_emission(tmp_path):
    from core.milestones import delivery
    with native_advice(tmp_path) as context:
        delivery.emitted({'additionalContext': context[:-8]})
    assert 'emission' not in attempts(tmp_path)[0]


def test_native_full_context_is_recorded_once_without_raw_text(tmp_path):
    from core.milestones import delivery
    with native_advice(tmp_path) as context:
        response = {'hookSpecificOutput': {'additionalContext': 'existing guidance\n' + context}}
        delivery.emitted(response)
        first = attempts(tmp_path)[0]['emission']
        delivery.emitted(response)
        assert attempts(tmp_path)[0]['emission'] == first
    assert context not in (tmp_path / '.elevenpowers/advice.json').read_text()


def test_changed_generation_cannot_receive_old_emission(tmp_path):
    from core.milestones import delivery
    with native_advice(tmp_path) as context:
        readiness.removed('claude', tmp_path)
        delivery.emitted({'additionalContext': context})
    assert 'emission' not in attempts(tmp_path)[0]


def test_missing_session_cannot_qualify_emission(tmp_path):
    from core.milestones import delivery
    ledger = project(tmp_path)
    with readiness.ingress('host'), delivery.collect():
        with readiness.callback('claude', tmp_path, 'PostToolUse', {}):
            context = deliver(ledger)
        delivery.emitted({'additionalContext': context})
    assert 'emission' not in attempts(tmp_path)[0]


def test_failed_stdout_flush_cannot_claim_emission(tmp_path, monkeypatch):
    from core.hosts import transport
    class BrokenOutput:
        def write(self, text):
            return len(text)
        def flush(self):
            raise BrokenPipeError('controlled flush failure')
    with native_advice(tmp_path) as context:
        with monkeypatch.context() as patch:
            patch.setattr(sys, 'stdout', BrokenOutput())
            with pytest.raises(BrokenPipeError):
                transport.emit('PostToolUse', {'additionalContext': context})
    assert 'emission' not in attempts(tmp_path)[0]


def test_many_emissions_keep_state_inside_its_read_budget(tmp_path):
    from core.milestones.automatic import _store, _read, digest
    from core.milestones.delivery import content_hash
    rows = []
    for index in range(20):
        rows.append({'id': digest(str(index)), 'attempts': [
            {'id': f'{index:016x}{number:016x}', 'key': digest([index, number]), 'at': 1,
             'status': 'delivered', 'context': content_hash('context'),
             'checks': [digest(n) for n in range(6)],
             'emission': {'host': 'claude', 'generation': 'a'*32, 'session': 'b'*64,
                          'runtime': 'c'*64, 'context': content_hash('context'), 'at': 2}}
            for number in range(10)]})
    target = tmp_path / 'advice.json'
    _store(target, {'schema': 1, 'tasks': json.loads(json.dumps(rows))})
    assert target.stat().st_size <= 65536
    value = _read(target)
    assert value['tasks'][-1]['id'] == digest('19')
    assert value['evicted_tasks'] > 0
    target.unlink()
    _store(target, {'schema': 1, 'tasks': rows}, keep_task=rows[0]['id'])
    assert any(task['id'] == rows[0]['id'] for task in _read(target)['tasks'])
