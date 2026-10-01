"""Independent review reproductions: each must be observed RED before correction."""
import json

import pytest

from test_project_health import prepared, captured


def test_mixed_verbose_failure_cannot_be_overridden_by_a_passing_test(tmp_path):
    from core.health import inspect
    from core.hook import dispatch
    from core.hosts.readiness import ingress
    prepared(tmp_path)
    captured(tmp_path)
    with ingress('host'):
        dispatch('PostToolUse', {'cwd': str(tmp_path), '_ep_platform': 'codex', 'session_id': 's',
                 'tool_name': 'Bash', 'tool_input': {'command': 'python -m pytest'}, 'tool_response': {
                 'stdout': 'test_a.py::test_bad FAILED\ntest_a.py::test_good PASSED\n1 failed, 1 passed in 0.1s', 'exit_code': 1}})
        dispatch('Stop', {'cwd': str(tmp_path), '_ep_platform': 'codex', 'session_id': 's'})
    value = inspect('codex', tmp_path)
    assert value['health']['stages']['verification']['state'] == 'failed'
    assert value['health']['state'] != 'observed'


def test_malformed_patch_records_remain_actionable(tmp_path):
    from core.health import inspect
    prepared(tmp_path)
    captured(tmp_path)
    (tmp_path / '.elevenpowers/patches.json').write_text(json.dumps({'pending': {'bad': []}}))
    value = inspect('codex', tmp_path)
    assert value['health']['state'] == 'incomplete'
    assert value['next_actions']


def test_corrupt_config_cannot_silently_become_a_valid_default(tmp_path):
    from core.health import inspect
    prepared(tmp_path)
    (tmp_path / 'pytest.ini').write_text('[pytest]\n')
    captured(tmp_path)
    assert inspect('codex', tmp_path)['health']['state'] == 'observed'
    (tmp_path / '.elevenpowers/config.json').write_text('{bad')
    value = inspect('codex', tmp_path)
    assert value['health']['state'] == 'incomplete'
    assert any('diagnostic' in x.lower() or 'config' in x.lower() for x in value['next_actions'])


def test_unresolved_current_phase_error_requires_same_phase_recovery(tmp_path):
    from core.health import inspect
    from core.hook import dispatch
    from core.hosts.readiness import callback, ingress
    prepared(tmp_path)
    captured(tmp_path)
    with ingress('host'), pytest.raises(OSError), callback('codex', tmp_path, 'PreToolUse', {'session_id': 's'}):
        raise OSError('failure')
    with ingress('host'):
        dispatch('Stop', {'cwd': str(tmp_path), '_ep_platform': 'codex', 'session_id': 's'})
    value = inspect('codex', tmp_path)
    assert value['health']['state'] != 'observed'
    assert any('PreToolUse' in x for x in value['next_actions'])
    with ingress('host'), callback('codex', tmp_path, 'PreToolUse', {'session_id': 's'}):
        pass
    assert inspect('codex', tmp_path)['health']['state'] == 'observed'


def test_acceptance_rechecks_the_contract_after_the_nested_health_read(tmp_path, monkeypatch):
    from core.hosts.acceptance import inspect
    from core import health
    from test_native_acceptance import exercise_history
    root = tmp_path / 'exercise'
    exercise_history(root, monkeypatch)
    real = health.inspect
    def moving(*args, **kwargs):
        value = real(*args, **kwargs)
        (root / 'check.py').write_text('# changed contract during inspection\n')
        return value
    monkeypatch.setattr(health, 'inspect', moving)
    value = inspect('codex', root)
    assert value['state'] == 'incomplete'
    assert value['next_actions']
