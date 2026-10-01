"""Health ordering, timing retention and cooperative read boundaries."""
import json

from test_project_health import prepared, captured


def test_a_new_command_requires_a_new_completion(tmp_path):
    from core.health import inspect
    from core.hook import dispatch
    from core.hosts.readiness import ingress
    prepared(tmp_path)
    captured(tmp_path)
    with ingress('host'):
        dispatch('PostToolUse', {'cwd': str(tmp_path), '_ep_platform': 'codex', 'session_id': 's',
                 'tool_name': 'Bash', 'tool_input': {'command': 'python -m pytest'},
                 'tool_response': {'stdout': '1 passed in 0.1s', 'exit_code': 0}})
    value = inspect('codex', tmp_path)
    assert value['health']['stages']['verification']['state'] == 'observed'
    assert value['health']['stages']['completion']['state'] == 'waiting'


def test_budget_includes_optional_metadata_and_edit_diagnostics(tmp_path, monkeypatch):
    from core import health
    prepared(tmp_path)
    captured(tmp_path)
    clock = health.time.monotonic
    advanced = [0]
    monkeypatch.setattr(health.time, 'monotonic', lambda: clock() + advanced[0])
    def metadata(*args):
        advanced[0] = 11
        return {'state': 'disabled'}
    monkeypatch.setattr(health, '_engines', metadata)
    value = health.inspect('codex', tmp_path)
    assert value['health']['state'] == 'incomplete'
    assert value['health']['stages']['report']['state'] == 'incomplete'
    assert any('deadline' in x.lower() for x in value['next_actions'])


def test_changes_to_edit_diagnostic_state_qualify_the_read(tmp_path, monkeypatch):
    from core import health
    prepared(tmp_path)
    captured(tmp_path)
    real = health.export.build
    def moving(*args, **kwargs):
        body = real(*args, **kwargs)
        (tmp_path / '.elevenpowers/patches.json').write_text(json.dumps({'pending': {}, 'gaps': {}}))
        return body
    monkeypatch.setattr(health.export, 'build', moving)
    assert health.inspect('codex', tmp_path)['health']['state'] == 'incomplete'


def test_automatic_timing_summary_uses_the_declared_retained_sample(tmp_path):
    from core.health import inspect
    prepared(tmp_path)
    captured(tmp_path)
    checks = [{'started': i, 'finished': i + 1} for i in range(100)]
    (tmp_path / '.elevenpowers/verification.json').write_text(json.dumps(
        {'task': 'task-one', 'status': 'completed', 'checks': checks}))
    value = inspect('codex', tmp_path)
    assert value['timings']['automatic_commands']['samples'] == value['timings']['sample_limit'] == 32
    assert value['timings']['automatic_commands']['median_ms'] == 1000


def test_repository_scan_limit_never_reports_all_observed(tmp_path):
    from core.config import Config, save
    from core.health import inspect
    prepared(tmp_path)
    for i in range(40):
        (tmp_path / f'module_{i}.py').write_text(f'value = {i}\n')
    save(tmp_path, Config(profile='off', commands={'tests': 'python -m pytest'},
                          scan={'max_files': 4}, strength={'enabled': False}))
    captured(tmp_path)
    value = inspect('codex', tmp_path)
    assert not value['coverage']['complete']
    assert value['health']['state'] == 'incomplete'
