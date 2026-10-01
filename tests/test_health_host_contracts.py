"""Real producers through five launcher contracts, not installed agent sessions."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from core.hosts.acceptance import inspect, prepare
from core.ledger import Ledger
from core.process import run

SOURCE = Path(__file__).resolve().parents[1]


def deliver(host, root, kind, inputs=None, response=None):
    base = {'cwd': str(root), 'session_id': 'contract-session'}
    events = {'start': 'SessionStart', 'edit': 'PostToolUse', 'command': 'PostToolUse', 'stop': 'Stop'}
    payload = {**base, 'tool_name': 'Edit' if kind == 'edit' else 'Bash',
               'tool_input': inputs or {}, 'tool_response': response or {}}
    if host == 'gemini':
        events.update(edit='AfterTool', command='AfterTool', stop='AfterAgent')
        payload['tool_name'] = 'replace' if kind == 'edit' else 'run_shell_command'
        payload['tool_response'] = {'llmContent': (response or {}).get('stdout', ''),
                                    'data': response or {}}
    elif host == 'cursor':
        events.update(start='sessionStart', edit='postToolUse', command='postToolUse', stop='stop')
        payload.update(conversation_id='contract-session', tool_name='Edit' if kind == 'edit' else 'Shell',
                       tool_output=response or {}, status='completed')
    elif host == 'copilot':
        events.update(start='sessionStart', edit='postToolUse', command='postToolUse', stop='agentStop')
        payload.update(sessionId='contract-session', toolName='edit' if kind == 'edit' else 'bash',
                       toolArgs=inputs or {}, toolResult={**(response or {}),
                       'textResultForLlm': (response or {}).get('stdout', '')}, stopReason='end_turn')
    launcher = [sys.executable, str(SOURCE / 'plugin/bin/ep_hook.py')] if host == 'claude' else [
        sys.executable, str(SOURCE / 'plugin/bin/ep_host.py'), host]
    done = subprocess.run([*launcher, events[kind]], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr
    if done.stdout.strip():
        json.loads(done.stdout)


@pytest.mark.parametrize('host', ['claude', 'codex', 'gemini', 'cursor', 'copilot'])
@pytest.mark.parametrize('language', ['python', 'javascript'])
def test_two_real_languages_cross_all_launcher_contracts(tmp_path, monkeypatch, host, language):
    if language == 'javascript' and not shutil.which('node'):
        pytest.skip('Node unavailable')
    monkeypatch.setenv('EP_PROFILE', 'off')  # Test receipt delivery independently of automatic checks.
    root = tmp_path / 'exercise'
    manifest = prepare(host, root, language, SOURCE, version='contract-test-version')
    Ledger(root=root, task='exercise-task').save()
    deliver(host, root, 'start')
    command = manifest['command']
    failed = run(command, cwd=root, timeout=15)
    assert failed.returncode == 1
    deliver(host, root, 'command', {'command': command}, {'stdout': failed.stdout, 'exit_code': failed.returncode})
    app = root / manifest['source_file']
    app.write_text(app.read_text().replace('value > 10', 'value >= 10'))
    deliver(host, root, 'edit', {'file_path': str(app)})
    passed = run(command, cwd=root, timeout=15)
    assert passed.returncode == 0
    deliver(host, root, 'command', {'command': command}, {'stdout': passed.stdout, 'exit_code': passed.returncode})
    (root / 'wait.flag').write_text('intentional interruption')
    with pytest.raises(subprocess.TimeoutExpired) as timed:
        run(command, cwd=root, timeout=1)
    (root / 'wait.flag').unlink()
    deliver(host, root, 'command', {'command': command}, {'stdout': timed.value.stdout or '', 'interrupted': True})
    assert inspect(host, root)['state'] == 'incomplete'
    app.write_text(app.read_text() + ('# later source edit\n' if language == 'python' else '// later source edit\n'))
    deliver(host, root, 'edit', {'file_path': str(app)})
    from core.health import inspect as health
    assert health(host, root)['latest_receipt']['freshness'] == 'stale'
    passed = run(command, cwd=root, timeout=15)
    deliver(host, root, 'command', {'command': command}, {'stdout': passed.stdout, 'exit_code': passed.returncode})
    deliver(host, root, 'stop')
    value = inspect(host, root)
    assert value['state'] == 'passed', value
    assert value['task_state'] == 'UNVERIFIED'
    assert all(value['outcomes'].values())
