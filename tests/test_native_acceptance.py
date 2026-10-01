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
