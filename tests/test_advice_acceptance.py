"""Preparation is model-free; advice qualification is a separate observation."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from core.hosts.acceptance import prepare, inspect
from core.hosts.setup import PATHS

SOURCE = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('host', PATHS)
def test_optional_advice_exercise_seals_declaration_and_starts_waiting(tmp_path, host):
    root = tmp_path / 'exercise'
    value = prepare(host, root, 'python', SOURCE, version='operator-version', advice=True)
    assert value['advice_requested'] is True
    config = json.loads((root / '.elevenpowers/config.json').read_text())
    assert config['milestone_advice']['enabled'] is True
    declarations = json.loads((root / 'elevenpowers.milestones.json').read_text())
    assert declarations['milestones'][0]['checks'][0]['command'] == value['command']
    assert value['milestone_declaration']
    result = inspect(host, root)
    assert result['state'] == 'waiting'
    assert result['milestone_advice']['state'] == 'waiting'
    assert 'cd "' in (root / 'EXERCISE.md').read_text()
    assert not (root / '.elevenpowers/advice.json').exists()


def test_javascript_advice_exercise_uses_actual_flipping_tests(tmp_path):
    if not shutil.which('node'):
        pytest.skip('Node unavailable')
    root = tmp_path / 'javascript'
    value = prepare('claude', root, 'javascript', SOURCE, advice=True)
    before = subprocess.run(value['command'], cwd=root, shell=True, capture_output=True, timeout=20)
    assert before.returncode == 1
    app = root / value['source_file']
    app.write_text(app.read_text().replace('value > 10', 'value >= 10'))
    after = subprocess.run('cd . && ' + value['command'], cwd=root, shell=True, capture_output=True, timeout=20)
    assert after.returncode == 0
    assert inspect('claude', root)['state'] != 'passed'


def test_changed_advice_declaration_invalidates_the_prepared_exercise(tmp_path):
    root = tmp_path / 'exercise'
    prepare('claude', root, 'python', SOURCE, advice=True)
    (root / 'elevenpowers.milestones.json').write_text('{}')
    result = inspect('claude', root)
    assert result['state'] == 'incomplete'
    assert any('declaration' in action.lower() for action in result['next_actions'])


def test_doctor_advice_option_is_preparation_only(tmp_path):
    done = subprocess.run([sys.executable, str(SOURCE / 'plugin/bin/ep_doctor.py'), '--advice',
                           '--platform', 'claude', '--cwd', str(tmp_path)],
                          capture_output=True, text=True, timeout=15)
    assert done.returncode != 0
    assert '--prepare-acceptance' in done.stderr
