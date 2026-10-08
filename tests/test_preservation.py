"""Staged controller controls; fake calls never qualify installed acceptance."""
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest


def api():
    assert importlib.util.find_spec('eval.preservation'), 'staged native controller is missing'
    from eval import preservation
    return preservation


def test_preparation_has_equal_inputs_and_explicit_assisted_wiring(tmp_path):
    p = api()
    batch = tmp_path / 'batch'
    protocol = p.prepare(batch, names=('queue',))
    ordinary = batch / 'queue-ordinary/candidate'
    assisted = batch / 'queue-assisted/candidate'
    for name in ('service.py', 'formatting.py', 'tests/test_core.py', 'elevenpowers.milestones.json'):
        assert (ordinary / name).read_bytes() == (assisted / name).read_bytes()
    assert not (ordinary / '.claude/settings.local.json').exists()
    assert 'elevenpowers-host' in (assisted / '.claude/settings.local.json').read_text()
    assert protocol['seconds_per_session'] == 480
    assert len(protocol['slots']) == 2
    with pytest.raises(ValueError, match='new'):
        p.prepare(batch, names=('queue',))


def test_sealed_public_tests_and_configuration_changes_are_rejected(tmp_path):
    p = api(); batch = tmp_path / 'batch'; protocol = p.prepare(batch, names=('queue',))
    slot = protocol['slots'][0]; root = batch / slot / 'candidate'
    p.verify(batch, slot)
    (root / 'tests/test_core.py').write_text('# weakened\n')
    with pytest.raises(ValueError, match='sealed'):
        p.verify(batch, slot)


def test_native_command_resumes_one_session_without_disabling_hooks(tmp_path):
    p = api()
    first = p.native_command('claude', tmp_path, 'request', 'a' * 32, 1)
    second = p.native_command('claude', tmp_path, 'request', 'a' * 32, 2)
    assert '--session-id' in first and '--resume' in second
    assert first[first.index('--session-id') + 1] == second[second.index('--resume') + 1]
    assert '--no-session-persistence' not in first and '--safe-mode' not in first
    assert first[first.index('--effort') + 1] == 'medium'
    assert first[first.index('--model') + 1] == 'claude-sonnet-5'


def test_prelaunch_scope_change_and_retry_cannot_launch_model(tmp_path, monkeypatch):
    p = api(); batch = tmp_path / 'batch'; protocol = p.prepare(batch, names=('queue',))
    slot = protocol['slots'][0]
    (batch / slot / 'candidate/elevenpowers.milestones.json').write_text('{}')
    monkeypatch.setattr(p.subscription, 'auth', lambda *a: pytest.fail('changed inputs reached authentication'))
    with pytest.raises(ValueError, match='sealed'):
        p.execute(batch, slot, 'claude')
    (batch / slot / 'result.json').write_text('{}')
    with pytest.raises(ValueError, match='attempt'):
        p.execute(batch, slot, 'claude')


def test_incomplete_pairs_cannot_establish_correctness_gain(tmp_path):
    p = api(); batch = tmp_path / 'batch'; p.prepare(batch, names=('queue',))
    value = p.summarize(batch)
    assert value['state'] == 'incomplete'
    assert value['paired_correctness_advantage_observed'] is False
    assert value['linked_correction_observed'] is False


def test_stage_journal_precedes_launch_and_resume_preserves_allowance(tmp_path, monkeypatch):
    p = api(); batch = tmp_path / 'batch'; protocol = p.prepare(batch, names=('queue',))
    slot = protocol['slots'][0]
    calls = []
    monkeypatch.setattr(p.subscription, 'auth', lambda *a: True)
    def launch(args, **kwargs):
        if '--version' in args:
            return subprocess.CompletedProcess(args, 0, '2.1.292 (Claude Code)', '')
        journal = json.loads((batch / slot / 'result.json').read_text())
        assert journal['stages'][-1]['state'] == 'running'
        stage = len(calls) + 1
        assert ('--session-id' if stage == 1 else '--resume') in args
        calls.append(kwargs['timeout'])
        from eval.preservation_cases import case
        (batch / slot / 'candidate/service.py').write_bytes(case('queue')['gold'][stage - 1].replace('\n', '\r\n').encode())
        output = json.dumps({'type': 'result', 'is_error': False, 'result': 'implemented',
                             'modelUsage': {'claude-sonnet-5': {}}})
        return subprocess.CompletedProcess(args, 0, output, '')
    monkeypatch.setattr(p, 'run', launch)
    result = p.execute(batch, slot, 'claude')
    assert result['state'] == 'completed' and len(calls) == 2
    assert calls[0] <= 240 and calls[1] <= 480
    assert result['model_seconds'] <= 480
    assert [s['independent_grade']['passed'] for s in result['stages']] == [6, 8]
    assert all(s['native']['state'] == 'incomplete' for s in result['stages'])
    for item in result['stages']:
        captured = json.loads((batch / slot / f"source-{item['stage']}.json").read_text())
        assert p._hash(captured['service.py'].encode()) == item['source_after']['service.py']
    with pytest.raises(ValueError, match='attempt'):
        p.execute(batch, slot, 'claude')


def test_timeout_is_retained_without_retrying_second_stage(tmp_path, monkeypatch):
    p = api(); batch = tmp_path / 'batch'; protocol = p.prepare(batch, names=('queue',))
    slot = protocol['slots'][0]
    monkeypatch.setattr(p.subscription, 'auth', lambda *a: True)
    def launch(args, **kwargs):
        if '--version' in args: return subprocess.CompletedProcess(args, 0, '2.1.292', '')
        raise subprocess.TimeoutExpired(args, kwargs['timeout'], output='partial')
    monkeypatch.setattr(p, 'run', launch)
    result = p.execute(batch, slot, 'claude')
    assert result['state'] == 'incomplete' and len(result['stages']) == 1
    assert result['stages'][0]['state'] == 'timeout'
    assert (batch / slot / 'native-1.jsonl').read_text() == 'partial'


def test_old_callbacks_from_another_session_cannot_qualify_stage(tmp_path, monkeypatch):
    p = api()
    protocol = {'runtime_fingerprint': 'a' * 64}
    phases = {name: {'processed': 1, 'session': 'b' * 64, 'last_at': 1}
              for name in ('SessionStart', 'PostToolUse', 'Stop')}
    phases['SessionStart']['runtime_fingerprint'] = 'a' * 64
    phases['PostToolUse']['edit'] = {'changed': 1, 'incomplete': False}
    monkeypatch.setattr(p, 'diagnostics', lambda root: {'claude': {'phases': phases, 'receipt_links': [{}]}})
    assert p._native(tmp_path, protocol)['state'] == 'incomplete'


def test_matching_current_callbacks_and_receipt_link_qualify_observation(tmp_path, monkeypatch):
    p = api(); session = 'current-session'; identity = p._hash(session.encode())
    protocol = {'runtime_fingerprint': 'a' * 64}
    phases = {name: {'processed': 1, 'session': identity, 'task': 'c' * 64, 'last_at': 11}
              for name in ('SessionStart', 'UserPromptSubmit', 'PostToolUse', 'Stop')}
    phases['SessionStart']['runtime_fingerprint'] = 'a' * 64
    phases['PostToolUse']['edit'] = {'changed': 1, 'incomplete': False, 'session': identity, 'task': 'c' * 64}
    monkeypatch.setattr(p, 'diagnostics', lambda root: {'claude': {'phases': phases,
        'receipt_links': [{'session': identity, 'task': 'c' * 64, 'at': 11}]}})
    assert p._native(tmp_path, protocol, since=10, session=session)['state'] == 'observed'
    phases['PostToolUse']['edit']['incomplete'] = True
    assert p._native(tmp_path, protocol, since=10, session=session)['state'] == 'incomplete'


def test_old_task_edit_cannot_be_reused_by_later_task_in_same_session(tmp_path, monkeypatch):
    p = api(); session = 'resumed'; identity = p._hash(session.encode())
    phases = {name: {'processed': 1, 'session': identity, 'task': 'c' * 64, 'last_at': 11}
              for name in ('SessionStart', 'UserPromptSubmit', 'PostToolUse', 'Stop')}
    phases['SessionStart']['runtime_fingerprint'] = 'a' * 64
    phases['PostToolUse']['edit'] = {'changed': 1, 'incomplete': False, 'session': identity, 'task': 'd' * 64}
    monkeypatch.setattr(p, 'diagnostics', lambda root: {'claude': {'phases': phases,
        'receipt_links': [{'session': identity, 'task': 'c' * 64, 'at': 11}]}})
    assert p._native(tmp_path, {'runtime_fingerprint': 'a' * 64}, since=10, session=session)['state'] == 'incomplete'


def test_loaded_budget_cannot_expand_approved_allowance(tmp_path):
    p = api(); batch = tmp_path / 'batch'; protocol = p.prepare(batch, names=('queue',))
    for value in (960, -1, True, '480', float('nan')):
        protocol['seconds_per_session'] = value
        (batch / 'protocol.json').write_text(json.dumps(protocol))
        with pytest.raises(ValueError, match='allowance'):
            p.verify(batch, protocol['slots'][0], initial=True)
    protocol['seconds_per_session'] = 240
    (batch / 'protocol.json').write_text(json.dumps(protocol))
    with pytest.raises(ValueError, match='sealed protocol'):
        p.verify(batch, protocol['slots'][0], initial=True)


def test_unsealed_extra_test_before_first_launch_breaks_equal_start(tmp_path):
    p = api(); batch = tmp_path / 'batch'; protocol = p.prepare(batch, names=('queue',))
    slot = protocol['slots'][0]
    (batch / slot / 'candidate/tests/test_added.py').write_text('assert False\n')
    with pytest.raises(ValueError, match='sealed'):
        p.verify(batch, slot, initial=True)
