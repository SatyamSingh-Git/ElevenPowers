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


def test_gemini_setup_preserves_settings_and_uses_native_names(tmp_path):
    from core.hosts.setup import install, remove
    path = tmp_path / ".gemini/settings.json"
    path.parent.mkdir()
    original = {"model": {"name": "user-choice"}, "hooks": {"BeforeTool": [{"hooks": [{"type": "command", "command": "user-hook", "name": "user"}]}]}}
    path.write_text(json.dumps(original))
    install("gemini", tmp_path, sys.executable, SOURCE)
    first = path.read_bytes()
    config = json.loads(first)
    handler = config["hooks"]["BeforeTool"][-1]["hooks"][0]
    assert handler["name"] == "elevenpowers-host"
    assert "statusMessage" not in handler
    assert handler["timeout"] == 20000
    install("gemini", tmp_path, sys.executable, SOURCE)
    assert path.read_bytes() == first
    remove("gemini", tmp_path)
    assert json.loads(path.read_text()) == original


def test_removal_preserves_foreign_handlers_in_a_shared_group(tmp_path):
    from core.hosts.setup import remove
    path = tmp_path / ".gemini/settings.json"
    path.parent.mkdir()
    foreign = {"type": "command", "command": "user command", "name": "user"}
    path.write_text(json.dumps({"hooks": {"BeforeTool": [{"matcher": "read_file", "hooks": [
        foreign, {"type": "command", "command": "ep", "name": "elevenpowers-host"}]}]}}))
    remove("gemini", tmp_path)
    assert json.loads(path.read_text())["hooks"]["BeforeTool"] == [{"matcher": "read_file", "hooks": [foreign]}]


def test_cursor_setup_preserves_flat_hooks_and_refuses_unknown_version(tmp_path):
    from core.hosts.setup import install, remove
    path = tmp_path / ".cursor/hooks.json"
    path.parent.mkdir()
    original = {"version": 1, "hooks": {"stop": [{"command": "user-hook"}]}}
    path.write_text(json.dumps(original))
    install("cursor", tmp_path, sys.executable, SOURCE)
    first = path.read_bytes()
    assert json.loads(first)["hooks"]["stop"][-1]["loop_limit"] == 2
    install("cursor", tmp_path, sys.executable, SOURCE)
    assert path.read_bytes() == first
    remove("cursor", tmp_path)
    assert json.loads(path.read_text()) == original
    original["version"] = 99
    path.write_text(json.dumps(original))
    before = path.read_bytes()
    with pytest.raises(ValueError, match="version"):
        install("cursor", tmp_path, sys.executable, SOURCE)
    assert path.read_bytes() == before
