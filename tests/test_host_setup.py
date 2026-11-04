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


def _store_python():
    import os
    folder = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps"
    for alias in sorted(folder.glob("PythonSoftwareFoundation.Python.*/python.exe")) if folder.is_dir() else []:
        try:
            alias.resolve(strict=True)
        except OSError:
            return alias
    return None


@pytest.mark.skipif(_store_python() is None, reason="needs a Microsoft Store Python, whose alias does not resolve")
def test_setup_launches_a_store_python_through_its_alias(tmp_path):
    import subprocess
    from core.hosts.setup import install
    path = install("codex", tmp_path, str(_store_python()), SOURCE)
    command = json.loads(path.read_text())["hooks"]["Stop"][0]["hooks"][0]["command"]
    result = subprocess.run(command, shell=True, input=json.dumps({"cwd": str(tmp_path)}),
                            text=True, capture_output=True, cwd=tmp_path, timeout=20)
    assert result.returncode == 0, result.stderr
    assert isinstance(json.loads(result.stdout), dict)


def test_setup_refuses_an_interpreter_that_does_not_exist(tmp_path):
    from core.hosts.setup import install
    with pytest.raises(ValueError, match="must exist"):
        install("codex", tmp_path, str(tmp_path / "missing" / "python.exe"), SOURCE)
    assert not (tmp_path / ".codex").exists()


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


def test_copilot_setup_merges_and_executes_direct_args(tmp_path):
    import subprocess
    from core.hosts.setup import install, remove
    path = tmp_path / ".github/hooks/elevenpowers.json"
    path.parent.mkdir(parents=True)
    original = {"version": 1, "hooks": {"agentStop": [{"type": "command", "exec": "user-hook", "args": []}]}}
    path.write_text(json.dumps(original))
    install("copilot", tmp_path, sys.executable, SOURCE)
    first = path.read_bytes()
    handler = json.loads(first)["hooks"]["agentStop"][-1]
    done = subprocess.run([handler["exec"], *handler["args"]], input=json.dumps({"cwd": str(tmp_path)}), text=True, capture_output=True, timeout=20)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout)["decision"] == "allow"
    install("copilot", tmp_path, sys.executable, SOURCE)
    assert path.read_bytes() == first
    remove("copilot", tmp_path)
    assert json.loads(path.read_text()) == original


def _stand_in(source):
    # Prints what it was given and exits 2, the code a Stop gate blocks with.
    launcher = source / "plugin/bin/ep_hook.py"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("import json, sys\nprint(json.dumps(sys.argv[1:]))\nsys.exit(2)\n")
    return source


def _git_bash():
    import shutil
    git = shutil.which("git")
    found = git and next((p / "bin/bash.exe" for p in Path(git).resolve().parents if (p / "bin/bash.exe").exists()), None)
    if not found:
        pytest.skip("Git Bash not found")
    return found


# Claude Code 2.1.292 on Windows runs hook commands through Git Bash; seen on 2026-11-03
# by a blocked-prompt hook that recorded its own parent processes.
@pytest.mark.skipif(sys.platform != "win32", reason="Windows hook command form")
@pytest.mark.parametrize("name, wrapped", [("plain-runtime", False), ("runtime space %EP_TEST% 'literal'", True)])
def test_claude_hooks_reach_python_through_git_bash_and_keep_exit_codes(tmp_path, name, wrapped):
    import subprocess
    from core.hosts.setup import install
    project = tmp_path / "project"
    project.mkdir()
    path = install("claude", project, sys.executable, _stand_in(tmp_path / name))
    command = json.loads(path.read_text())["hooks"]["Stop"][0]["hooks"][0]["command"]
    assert command.lower().startswith("powershell") is wrapped
    done = subprocess.run([str(_git_bash()), "-c", command], input="{}", text=True, capture_output=True, timeout=30)
    assert (done.returncode, json.loads(done.stdout)) == (2, ["Stop"]), done.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows hook command form")
def test_hosts_not_shown_to_use_git_bash_keep_the_encoded_command(tmp_path):
    from core.hosts.setup import WINDOWS_PREFIX, install
    path = install("codex", tmp_path, sys.executable, SOURCE)
    assert json.loads(path.read_text())["hooks"]["Stop"][0]["hooks"][0]["command"].startswith(WINDOWS_PREFIX)


@pytest.mark.parametrize("name", ["R&D", "runtime space %EP_TEST% 'literal'", "runtime Ω"])
def test_setup_launches_source_with_shell_metacharacters(tmp_path, name):
    import subprocess
    from core.hosts.setup import install
    from core.hosts.package import build
    source = build("codex", tmp_path / name)
    path = install("codex", tmp_path, sys.executable, source)
    command = json.loads(path.read_text())["hooks"]["Stop"][0]["hooks"][0]["command"]
    done = subprocess.run(command, shell=True, input=json.dumps({"cwd": str(tmp_path)}), text=True, capture_output=True, timeout=20)
    assert done.returncode == 0, done.stderr
    assert isinstance(json.loads(done.stdout), dict)
