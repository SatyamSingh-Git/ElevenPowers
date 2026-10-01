import json
from pathlib import Path
import subprocess
import sys

import pytest

SOURCE = Path(__file__).resolve().parents[1]


def test_activation_waits_then_records_processed_startup(tmp_path):
    from core.hosts.setup import install
    from core.hosts.readiness import activation, ingress
    from core.hosts.bridge import run
    install('codex', tmp_path, sys.executable, SOURCE)
    assert activation('codex', tmp_path)['state'] == 'waiting'
    with ingress('host'):
        run('codex', 'SessionStart', {'cwd': str(tmp_path), 'session_id': 'private-session'})
    live = activation('codex', tmp_path)
    assert live['state'] == 'active'
    assert live['last_event'] == 'SessionStart'
    assert live['received'] == 1
    assert 'private-session' not in (tmp_path / '.elevenpowers/integrations.json').read_text()


def test_fixtures_and_replay_do_not_activate_project(tmp_path):
    from core.hosts.setup import install
    from core.hosts.readiness import activation, ingress
    from core.hosts.bridge import run
    install('codex', tmp_path, sys.executable, SOURCE)
    run('codex', 'SessionStart', {'cwd': str(tmp_path)})
    with ingress('replay'):
        run('codex', 'SessionStart', {'cwd': str(tmp_path)})
    assert activation('codex', tmp_path)['state'] == 'waiting'


def test_reinstall_is_idempotent_but_changed_wiring_resets_activation(tmp_path):
    from core.hosts.setup import install
    from core.hosts.readiness import activation, ingress
    from core.hosts.bridge import run
    path = install('codex', tmp_path, sys.executable, SOURCE)
    with ingress('host'):
        run('codex', 'SessionStart', {'cwd': str(tmp_path)})
    install('codex', tmp_path, sys.executable, SOURCE)
    assert activation('codex', tmp_path)['state'] == 'active'
    config = json.loads(path.read_text())
    config['hooks']['Stop'] = []
    path.write_text(json.dumps(config))
    install('codex', tmp_path, sys.executable, SOURCE)
    assert activation('codex', tmp_path)['state'] == 'waiting'


def test_failed_processing_is_actionable(tmp_path, monkeypatch):
    from core import hook
    from core.hosts.readiness import activation, ingress
    def broken(*_):
        raise OSError('secret-raw-error')
    monkeypatch.setattr(hook, 'on_session_start', broken)
    with ingress('host'), pytest.raises(OSError):
        hook.dispatch('SessionStart', {'cwd': str(tmp_path), '_ep_platform': 'codex'})
    live = activation('codex', tmp_path)
    assert live['state'] == 'error'
    assert live['error'] == 'OSError'
    assert 'secret-raw-error' not in (tmp_path / '.elevenpowers/integrations.json').read_text()


def test_claude_setup_preserves_user_configuration_and_removes_only_ours(tmp_path):
    from core.hosts.setup import install, remove
    from core.hosts.doctor import report
    path = tmp_path / '.claude/settings.local.json'
    path.parent.mkdir()
    original = {'permissions': {'allow': ['Read']}, 'hooks': {'Stop': [{'hooks': [
        {'type': 'command', 'command': 'user-hook'}]}]}}
    path.write_text(json.dumps(original))
    install('claude', tmp_path, sys.executable, SOURCE)
    assert report('claude', tmp_path)[1]
    first = path.read_bytes()
    install('claude', tmp_path, sys.executable, SOURCE)
    assert path.read_bytes() == first
    remove('claude', tmp_path)
    assert json.loads(path.read_text()) == original


def test_auto_selection_refuses_ambiguity(tmp_path, monkeypatch):
    from core.hosts.onboarding import select_host
    monkeypatch.setattr('shutil.which', lambda name: '/bin/' + name if name in {'claude', 'codex'} else None)
    with pytest.raises(ValueError, match='multiple'):
        select_host('auto', tmp_path)
    assert select_host('codex', tmp_path) == 'codex'


def test_readiness_reports_commands_coverage_and_next_action(tmp_path):
    from core.hosts.setup import install
    from core.hosts.onboarding import report
    (tmp_path / 'package.json').write_text(json.dumps({'scripts': {'ci': 'node check.js'}}))
    install('codex', tmp_path, sys.executable, SOURCE)
    text = report('codex', tmp_path)
    assert 'npm run ci' in text
    assert 'waiting' in text
    assert 'coverage: complete' in text.lower()
    assert 'Next action:' in text
    assert str(tmp_path.resolve()) in text


def test_native_launcher_records_callback_but_explicit_replay_does_not(tmp_path):
    from core.hosts.setup import install
    from core.hosts.readiness import activation
    install('codex', tmp_path, sys.executable, SOURCE)
    args = [sys.executable, str(SOURCE / 'plugin/bin/ep_host.py'), 'codex', 'SessionStart']
    payload = json.dumps({'cwd': str(tmp_path)})
    done = subprocess.run([*args, '--replay'], input=payload, text=True, capture_output=True, timeout=20)
    assert done.returncode == 0, done.stderr
    assert activation('codex', tmp_path)['state'] == 'waiting'
    done = subprocess.run(args, input=payload, text=True, capture_output=True, timeout=20)
    assert done.returncode == 0, done.stderr
    assert activation('codex', tmp_path)['state'] == 'active'


def test_removed_hooks_do_not_still_report_active(tmp_path):
    from core.hosts.setup import install, remove
    from core.hosts.readiness import activation, ingress
    from core.hosts.bridge import run
    install('codex', tmp_path, sys.executable, SOURCE)
    with ingress('host'):
        run('codex', 'SessionStart', {'cwd': str(tmp_path)})
    remove('codex', tmp_path)
    assert activation('codex', tmp_path)['state'] == 'removed'


def test_doctor_rejects_matcher_that_prevents_claude_callbacks(tmp_path):
    from core.hosts.setup import install
    from core.hosts.doctor import report
    path = install('claude', tmp_path, sys.executable, SOURCE)
    value = json.loads(path.read_text())
    value['hooks']['PostToolUse'][0]['matcher'] = 'NeverCalled'
    path.write_text(json.dumps(value))
    assert not report('claude', tmp_path)[1]


def test_quoted_interpreter_is_reported_available(tmp_path):
    from core.config import Config, save
    from core.hosts.onboarding import inspect
    save(tmp_path, Config(commands={'tests': f'"{sys.executable}" -m pytest'}))
    result = inspect('codex', tmp_path)
    assert result['runtimes'] == {sys.executable: True}
    assert not any('Install or activate' in action for action in result['next_actions'])


def test_callback_registry_refuses_unbounded_host_names(tmp_path):
    from core.hosts.readiness import callback, ingress
    with ingress('host'), pytest.raises(ValueError, match='unsupported'):
        with callback('arbitrary-user-supplied-platform', tmp_path, 'SessionStart'):
            pass
    assert not (tmp_path / '.elevenpowers/integrations.json').exists()
