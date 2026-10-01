"""Generalized onboarding controls across manifests and concurrent launchers."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

import pytest

from core.hosts.onboarding import inspect
from core.hosts.readiness import activation
from core.hosts.setup import install

SOURCE = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('manifest,content,command', [
    ('package.json', '{"scripts":{"ci":"node check.js"}}', 'npm run ci'),
    ('pyproject.toml', '[tool.pytest.ini_options]\ntestpaths=["tests"]\n', 'python -m pytest'),
    ('Cargo.toml', '[package]\nname="example"\nversion="0.1.0"\n', 'cargo test'),
    ('go.mod', 'module example.test/project\n\ngo 1.22\n', 'go test ./...'),
])
def test_readiness_discovers_each_projects_manifest_without_running_it(tmp_path, manifest, content, command):
    project = tmp_path / 'an unrelated project'
    project.mkdir()
    (project / manifest).write_text(content)
    value = inspect('codex', project)
    assert value['commands']['tests'] == command
    assert value['coverage']['complete']
    assert not (project / '.elevenpowers').exists()


def test_parallel_callbacks_preserve_all_activation_updates(tmp_path):
    install('codex', tmp_path, sys.executable, SOURCE)
    launcher = SOURCE / 'plugin/bin/ep_host.py'
    def call(index):
        payload = json.dumps({'cwd': str(tmp_path), 'session_id': f'private-{index}', 'prompt': ''})
        return subprocess.run([sys.executable, str(launcher), 'codex', 'UserPromptSubmit'],
                              input=payload, text=True, capture_output=True, timeout=20)
    with ThreadPoolExecutor(max_workers=6) as workers:
        results = list(workers.map(call, range(12)))
    assert all(result.returncode == 0 for result in results), [r.stderr for r in results]
    value = activation('codex', tmp_path)
    assert value['received'] == value['processed'] == 12
    assert value['state'] == 'received'
    assert 'private-' not in (tmp_path / '.elevenpowers/integrations.json').read_text()


def test_callbacks_in_one_project_do_not_activate_another(tmp_path):
    first, second = tmp_path / 'first', tmp_path / 'second'
    first.mkdir()
    second.mkdir()
    install('codex', first, sys.executable, SOURCE)
    install('codex', second, sys.executable, SOURCE)
    done = subprocess.run([sys.executable, str(SOURCE / 'plugin/bin/ep_host.py'), 'codex', 'SessionStart'],
                          input=json.dumps({'cwd': str(first)}), text=True, capture_output=True, timeout=20)
    assert done.returncode == 0, done.stderr
    assert activation('codex', first)['state'] == 'active'
    assert activation('codex', second)['state'] == 'waiting'
