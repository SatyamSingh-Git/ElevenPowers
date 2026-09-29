"""Codex documented hook contracts; these are not live-session captures."""
from pathlib import Path

import pytest


def adapter():
    from core.hosts import codex
    return codex


def test_codex_requires_explicit_existing_root(tmp_path):
    host = adapter()
    event = host.normalize("SessionStart", {"cwd": str(tmp_path)})
    assert event.root == tmp_path.resolve()
    assert event.phase == "SessionStart"
    with pytest.raises(ValueError, match="root"):
        host.normalize("SessionStart", {})
    with pytest.raises(ValueError, match="root"):
        host.normalize("SessionStart", {"cwd": str(tmp_path / "missing")})


def test_codex_maps_shell_and_patch_without_guessing_paths(tmp_path):
    host = adapter()
    shell = host.normalize("PostToolUse", {
        "cwd": str(tmp_path), "tool_name": "Bash", "tool_input": {"command": "npm run ci"}})
    assert shell.payload["tool_name"] == "Bash"
    assert shell.payload["tool_input"]["command"] == "npm run ci"
    patch = host.normalize("PostToolUse", {
        "cwd": str(tmp_path), "tool_name": "apply_patch", "tool_input": {"command": "patch text"}})
    assert patch.payload["tool_name"] == "Patch"
    assert patch.payload["tool_input"].get("file_path") is None
    with pytest.raises(ValueError, match="event"):
        host.normalize("InventedEvent", {"cwd": str(tmp_path)})


def test_codex_prompt_preserves_identity_and_rejects_relative_root(tmp_path):
    event = adapter().normalize("UserPromptSubmit", {
        "cwd": str(tmp_path), "prompt": "fix bug", "session_id": "s", "turn_id": "t"})
    assert event.payload["prompt"] == "fix bug"
    assert event.payload["session_id"] == "s"
    with pytest.raises(ValueError, match="root"):
        adapter().normalize("SessionStart", {"cwd": "."})


@pytest.mark.parametrize("raw,state,code", [
    ({"exit_code": 0, "stdout": "ok"}, "passed", 0),
    ({"exit_code": 2, "output": "bad"}, "failed", 2),
    ({"exit_code": None, "session_id": 42, "output": "partial"}, "running", None),
    ({"stdout": "all good"}, "unknown", None),
    ({"exit_code": True}, "unknown", None),
    ({"exit_code": "0"}, "unknown", None),
    ({"exit_code": 0, "timed_out": True}, "interrupted", None),
    ("Process exited with code 0\nOutput:\nok", "unknown", None),
])
def test_codex_outcomes_do_not_assume_success(raw, state, code):
    result = adapter().outcome({"tool_response": raw})
    assert (result.state, result.exit_code) == (state, code)
    if code is None:
        assert result.result()["interrupted"] is True


def test_codex_normalized_receipt_carries_only_explicit_status(tmp_path):
    event = adapter().normalize("PostToolUse", {
        "cwd": str(tmp_path), "tool_name": "Bash", "tool_input": {"command": "npm run ci"},
        "tool_response": {"exit_code": 1, "stdout": "failed"}})
    assert event.payload["tool_response"] == {"exit_code": 1, "stdout": "failed"}
