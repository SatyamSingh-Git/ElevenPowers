"""Installation should activate useful defaults without project-specific setup."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.config import Config, load, save
from core.evidence import Kind, Result, scan_sources
from core.parsers import parse


def package(root, scripts, **extra):
    (root / "package.json").write_text(json.dumps({"scripts": scripts, **extra}), encoding="utf-8")


def test_default_scan_handles_large_project_without_configuration(tmp_path):
    # Sparse fixture tests the selection budget without hashing or allocating it.
    with (tmp_path / "fixture.json").open("wb") as stream:
        stream.truncate(80 * 1024 * 1024)
    assert scan_sources(tmp_path).complete
    save(tmp_path, Config(scan={"max_bytes": 1024}))
    assert not scan_sources(tmp_path).complete


def test_startup_announces_health_and_discovered_command_through_launcher(tmp_path):
    package(tmp_path, {"ci": "checks"})
    launcher = Path(__file__).resolve().parents[1] / "plugin/bin/ep_hook.py"
    done = subprocess.run([sys.executable, str(launcher), "SessionStart"],
                          input=json.dumps({"cwd": str(tmp_path)}), capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    context = json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "ElevenPowers active" in context and "npm run ci" in context
    assert "coverage" in context and "health" in context
    assert (tmp_path / ".elevenpowers/.gitignore").exists()
    assert not (tmp_path / ".elevenpowers/config.json").exists()


def test_passive_startup_does_not_run_health_work(tmp_path, monkeypatch, capsys):
    from core import hook
    save(tmp_path, Config(profile="off"))
    monkeypatch.setattr(hook, "snapshot", lambda *a: pytest.fail("passive checkpoint"))
    assert hook.on_session_start({}, tmp_path) == 0
    assert capsys.readouterr().out == ""


def test_observation_hooks_allow_cold_repository_scan():
    from core.wiring import hooks_json
    hooks = hooks_json()["hooks"]
    assert hooks["PostToolUse"][0]["hooks"][0]["timeout"] >= 120
    assert hooks["PostToolUseFailure"][0]["hooks"][0]["timeout"] >= 120


def test_startup_reports_missing_detected_runtime(tmp_path, monkeypatch, capsys):
    from core import hook
    import shutil
    package(tmp_path, {"ci": "checks"})
    monkeypatch.setattr(shutil, "which", lambda executable: None)
    hook.on_session_start({}, tmp_path)
    output = capsys.readouterr().out
    assert "npm" in output and "not found on PATH" in output


