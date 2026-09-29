import json
from pathlib import Path
import sys

import pytest

SOURCE = Path(__file__).resolve().parents[1]


def test_codex_setup_is_idempotent_and_preserves_other_hooks(tmp_path):
    from core.hosts.setup import install, remove
    path = tmp_path / ".codex/hooks.json"
    path.parent.mkdir()
    original = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "other"}]}]}, "other": 7}
    path.write_text(json.dumps(original))
    install("codex", tmp_path, sys.executable, SOURCE)
    first = path.read_bytes()
    install("codex", tmp_path, sys.executable, SOURCE)
    assert path.read_bytes() == first
    remove("codex", tmp_path)
    assert json.loads(path.read_text()) == original


def test_codex_setup_refuses_malformed_configuration(tmp_path):
    from core.hosts.setup import install
    path = tmp_path / ".codex/hooks.json"
    path.parent.mkdir()
    path.write_text('{broken')
    with pytest.raises(ValueError):
        install("codex", tmp_path, sys.executable, SOURCE)
    assert path.read_text() == '{broken'


def test_codex_setup_launches_quoted_paths(tmp_path):
    import subprocess
    from core.hosts.setup import install
    project = tmp_path / "project space"
    project.mkdir()
    path = install("codex", project, sys.executable, SOURCE)
    config = json.loads(path.read_text())
    command = config["hooks"]["Stop"][0]["hooks"][0]["command"]
    result = subprocess.run(command, shell=True, input=json.dumps({"cwd": str(project)}),
                            text=True, capture_output=True, cwd=project, timeout=20)
    assert result.returncode == 0, result.stderr
    assert isinstance(json.loads(result.stdout), dict)
