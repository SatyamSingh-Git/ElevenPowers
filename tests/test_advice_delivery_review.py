"""Review regressions: visible recommendations and optional-state isolation."""
import json

import pytest

from core import health
from core.milestones import advice, automatic, delivery
from test_advice_followup import emitted_project, inspect
from test_project_health import prepared


def report(commands):
    return {'state': 'UNVERIFIED', 'coverage': {'complete': True, 'issues': []},
            'rechecks': {'commands': [
                {'kind': 'suite', 'command': command, 'priority': 'high',
                 'milestones': [{'id': 'm' * 40, 'state': 'absent'} for _ in range(8)],
                 'reasons': [{'milestone': 'm' * 40, 'input': 'x' * 180, 'category': 'changed'}
                             for _ in range(3)]}
                for command in commands]}}


def test_only_complete_visible_command_lines_qualify():
    commands = ['python command_' + str(i) + '_' + 'x' * 310 for i in range(6)]
    context, selected = advice.render_with_checks(report(commands))
    assert context == advice.render(report(commands)) and len(context) <= 6000
    assert 0 < len(selected) < 6
    assert [row['command'] for row in selected] == [c for c in commands if c in context]


def test_previewed_command_cannot_qualify_as_exact_recommendation():
    context, selected = advice.render_with_checks(report(['python ' + 'x' * 400, 'python ok.py']))
    assert 'truncated preview' in context
    assert [row['command'] for row in selected] == ['python ok.py']


def test_oversized_optional_advice_does_not_degrade_required_health(tmp_path):
    prepared(tmp_path)
    before = health.inspect('codex', tmp_path)
    (tmp_path / '.elevenpowers/advice.json').write_bytes(b'x' * (8 * 1024 * 1024 + 1))
    after = health.inspect('codex', tmp_path)
    assert before['task'] == after['task'] == 'task-one'
    assert before['health'] == after['health']
    assert after['milestone_advice']['state'] == 'unconfigured'


@pytest.mark.parametrize('filename', ['.elevenpowers/advice.json', 'elevenpowers.milestones.json'])
def test_moving_optional_state_invalidates_only_advice_view(tmp_path, monkeypatch, filename):
    emitted_project(tmp_path)
    read = automatic._read
    def moving(path):
        value = read(path)
        target = tmp_path / filename
        saved = json.loads(target.read_text())
        target.write_text(json.dumps(saved) + '\n')
        return value
    monkeypatch.setattr(automatic, '_read', moving)
    result = inspect(tmp_path)
    assert result['state'] == 'incomplete'
    assert 'changed during' in ' '.join(result['issues'])


def test_declaration_changed_after_initial_seal_read_invalidates_acceptance(tmp_path, monkeypatch):
    from core.hosts import acceptance
    from pathlib import Path
    root = tmp_path / 'exercise'
    acceptance.prepare('claude', root, 'python', Path(__file__).resolve().parents[1], advice=True)
    original = acceptance._fingerprint
    calls = 0
    def changed(project, name):
        nonlocal calls
        result = original(project, name)
        if name == 'elevenpowers.milestones.json':
            calls += 1
            if calls == 1:
                (root / name).write_text('{}')
        return result
    monkeypatch.setattr(acceptance, '_fingerprint', changed)
    result = acceptance.inspect('claude', root)
    assert result['state'] == 'incomplete'
    assert any('changed' in action.lower() for action in result['next_actions'])
