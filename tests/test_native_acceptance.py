"""Real language producers and native-exercise qualification."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

SOURCE = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('language', ['python', 'javascript'])
def test_preparation_runs_no_host_and_actual_tests_flip(tmp_path, language, monkeypatch):
    from core.hosts.acceptance import prepare
    if language == 'javascript' and not shutil.which('node'):
        pytest.skip('Node unavailable')
    root = tmp_path / 'exercise'
    value = prepare('codex', root, language, SOURCE, version='operator-version')
    assert value['state'] == 'prepared'
    assert json.loads((root / '.elevenpowers/integrations.json').read_text())['codex']['state'] == 'waiting'
    before = subprocess.run(value['command'], cwd=root, shell=True, capture_output=True, text=True, timeout=15)
    assert before.returncode == 1
    app = root / value['source_file']
    app.write_text(app.read_text().replace('value > 10', 'value >= 10'))
    after = subprocess.run(value['command'], cwd=root, shell=True, capture_output=True, text=True, timeout=15)
    assert after.returncode == 0 and 'ok' in (after.stdout + after.stderr).lower()
    assert json.loads((root / '.elevenpowers/integrations.json').read_text())['codex']['state'] == 'waiting'
    assert 'operator-version' in (root / '.elevenpowers/acceptance.json').read_text()


def test_preparation_refuses_existing_or_linked_destination(tmp_path):
    from core.hosts.acceptance import prepare
    existing = tmp_path / 'existing'
    existing.mkdir()
    (existing / 'keep.txt').write_text('keep')
    with pytest.raises(ValueError, match='exist'):
        prepare('codex', existing, 'python', SOURCE)
    assert (existing / 'keep.txt').read_text() == 'keep'
    with pytest.raises(ValueError, match='language'):
        prepare('codex', tmp_path / 'wrong', 'unknown', SOURCE)
    assert not (tmp_path / 'wrong').exists()


def test_prepared_and_replayed_exercise_is_not_native_acceptance(tmp_path):
    from core.hosts.acceptance import prepare, inspect
    from core.hosts.bridge import run
    from core.hosts.readiness import ingress
    root = tmp_path / 'exercise'
    prepare('codex', root, 'python', SOURCE)
    assert inspect('codex', root)['state'] == 'waiting'
    with ingress('replay'):
        run('codex', 'SessionStart', {'cwd': str(root), 'session_id': 's'})
    assert inspect('codex', root)['state'] == 'waiting'


def exercise_history(root, monkeypatch, outcomes=('fail', 'pass', 'incomplete', 'pass')):
    """Canonical callback contract control, not an installed host session."""
    from core.hosts.acceptance import prepare
    from core.hosts.readiness import ingress
    from core.hook import dispatch
    from core.ledger import Ledger
    monkeypatch.setenv('EP_PROFILE', 'off')
    manifest = prepare('codex', root, 'python', SOURCE, version='operator-version')
    Ledger(root=root, task='exercise-task').save()
    payload = {'cwd': str(root), '_ep_platform': 'codex', 'session_id': 'contract-session'}
    with ingress('host'):
        dispatch('SessionStart', payload.copy())
        for outcome in outcomes:
            if outcome == 'pass':
                app = root / 'app.py'
                app.write_text(app.read_text().replace('value > 10', 'value >= 10'))
            dispatch('PostToolUse', {**payload, 'tool_name': 'Edit', 'tool_input': {'file_path': str(root / 'app.py')}})
            if outcome == 'incomplete':
                response = {'stdout': '', 'interrupted': True}
            else:
                done = subprocess.run(manifest['command'], cwd=root, shell=True, capture_output=True, text=True, timeout=15)
                response = {'stdout': done.stdout, 'stderr': done.stderr, 'exit_code': done.returncode}
                assert done.returncode == (1 if outcome == 'fail' else 0)
            dispatch('PostToolUse', {**payload, 'tool_name': 'Bash',
                                    'tool_input': {'command': manifest['command']}, 'tool_response': response})
        dispatch('Stop', payload.copy())
    return manifest


def test_acceptance_requires_outcomes_current_task_and_fresh_completion(tmp_path, monkeypatch):
    from core.hosts.acceptance import inspect
    from core.ledger import Ledger
    root = tmp_path / 'exercise'
    exercise_history(root, monkeypatch)
    before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    value = inspect('codex', root)
    assert value['state'] == 'passed', value
    assert all(value['outcomes'].values())
    assert value['version_source'] == 'operator'
    assert before == {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    (root / 'app.py').write_text((root / 'app.py').read_text() + '# another edit\n')
    assert inspect('codex', root)['state'] == 'incomplete'
    ledger = Ledger.load(root)
    ledger.task = 'other-task'
    ledger.save()
    assert inspect('codex', root)['state'] != 'passed'


@pytest.mark.parametrize('change', ['wiring', 'test', 'config', 'manifest'])
def test_changed_or_malformed_exercise_is_explicit(tmp_path, monkeypatch, change):
    from core.hosts.acceptance import inspect
    root = tmp_path / 'exercise'
    exercise_history(root, monkeypatch)
    path = {'wiring': '.codex/hooks.json', 'test': 'check.py',
            'config': '.elevenpowers/config.json', 'manifest': '.elevenpowers/acceptance.json'}[change]
    (root / path).write_text('{}' if change != 'test' else '# changed contract\n')
    value = inspect('codex', root)
    assert value['state'] == 'incomplete'
    assert value['next_actions']


def test_missing_incomplete_outcome_or_version_remains_unqualified(tmp_path, monkeypatch):
    from core.hosts.acceptance import inspect
    root = tmp_path / 'exercise'
    exercise_history(root, monkeypatch, outcomes=('fail', 'pass'))
    value = inspect('codex', root)
    assert value['state'] == 'waiting' and not value['outcomes']['incomplete']
    path = root / '.elevenpowers/acceptance.json'
    manifest = json.loads(path.read_text())
    manifest['host_version'], manifest['version_source'] = 'unavailable', 'unavailable'
    path.write_text(json.dumps(manifest))
    assert not inspect('codex', root)['checks']['host_version']
