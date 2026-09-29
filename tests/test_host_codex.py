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


def test_codex_responses_follow_native_contract():
    host = adapter()
    message = {"event": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "review"}
    assert host.render("PreToolUse", [message], 0, "")["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert host.render("Stop", [], 2, "checks missing") == {"decision": "block", "reason": "checks missing"}
    assert host.render("Stop", [{"systemMessage": "VERIFIED"}], 0, "") == {"systemMessage": "VERIFIED"}
    result = host.render("PostToolUse", [{"additionalContext": "observed"}], 0, "")
    assert result["hookSpecificOutput"]["additionalContext"] == "observed"
    assert "decision" not in result


def test_codex_bridge_collects_engine_response_without_claude_stdout(tmp_path, monkeypatch, capsys):
    from core.hosts.bridge import run
    from core import hook
    def handler(payload, root):
        assert root == tmp_path.resolve()
        hook._emit("Stop", systemMessage="UNVERIFIED")
        return 0
    monkeypatch.setattr(hook, "on_stop", handler)
    response, code = run("codex", "Stop", {"cwd": str(tmp_path)})
    assert (response, code) == ({"systemMessage": "UNVERIFIED"}, 0)
    assert capsys.readouterr().out == ""


def test_codex_continuation_does_not_open_a_new_task(tmp_path, monkeypatch):
    from core.hosts.bridge import run
    from core import hook
    monkeypatch.setattr(hook, "on_stop", lambda p, r: hook.transport.block("fix the failing test"))
    run("codex", "Stop", {"cwd": str(tmp_path), "session_id": "s"})
    monkeypatch.setattr(hook, "on_prompt", lambda *a: pytest.fail("continuation reset task"))
    assert run("codex", "UserPromptSubmit", {"cwd": str(tmp_path), "session_id": "s", "prompt": "fix the failing test"}) == ({}, 0)


def test_codex_duplicate_result_cannot_be_rebound_after_source_change(tmp_path):
    from core.hosts.bridge import run
    from core.config import Config, save
    from core.ledger import Ledger
    save(tmp_path, Config(profile="off", commands={"tests": "npm run ci"}))
    source = tmp_path / "app.py"
    source.write_text("x = 1\n")
    payload = {"cwd": str(tmp_path), "session_id": "s", "tool_use_id": "tool1", "tool_name": "Bash",
               "tool_input": {"command": "npm run ci"}, "tool_response": {"exit_code": 0}}
    run("codex", "PostToolUse", payload)
    before = Ledger.load(tmp_path).evidence[-1].to_dict()
    source.write_text("x = 2\n")
    run("codex", "PostToolUse", payload)
    assert len(Ledger.load(tmp_path).evidence) == 1
    assert Ledger.load(tmp_path).evidence[-1].to_dict() == before


def test_codex_different_execution_directory_remains_incomplete(tmp_path):
    child = tmp_path / "child"
    child.mkdir()
    event = adapter().normalize("PostToolUse", {"cwd": str(tmp_path), "tool_name": "Bash",
        "tool_input": {"command": "npm run ci", "workdir": str(child)}, "tool_response": {"exit_code": 0}})
    assert event.payload["tool_response"].get("interrupted") is True
