"""Cursor Agent native schema contracts; no live session capture implied."""
import json
import pytest


def adapter():
    from core.hosts import cursor
    return cursor


def test_cursor_unique_workspace_and_explicit_cwd(tmp_path):
    event = adapter().normalize("sessionStart", {"workspace_roots": [str(tmp_path)], "conversation_id": "c"})
    assert event.root == tmp_path.resolve()
    assert event.payload["session_id"] == "c"
    assert event.phase == "SessionStart"


def test_cursor_ambiguous_workspace_requires_cwd(tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(ValueError, match="root"):
        adapter().normalize("stop", {"workspace_roots": [str(tmp_path), str(other)]})
    event = adapter().normalize("stop", {"workspace_roots": [str(tmp_path), str(other)], "cwd": str(other), "status": "completed"})
    assert event.root == other.resolve()


def test_cursor_maps_prompt_shell_and_file_tools(tmp_path):
    host = adapter()
    prompt = host.normalize("beforeSubmitPrompt", {"workspace_roots": [str(tmp_path)], "prompt": "fix bug"})
    assert prompt.phase == "UserPromptSubmit"
    shell = host.normalize("preToolUse", {"cwd": str(tmp_path), "tool_name": "Shell", "tool_input": {"command": "npm run ci"}})
    assert shell.payload["tool_name"] == "Bash"
    file = host.normalize("postToolUse", {"cwd": str(tmp_path), "tool_name": "Write", "tool_input": {"file_path": "app.py"}})
    assert file.payload["tool_name"] == "Write"


@pytest.mark.parametrize("payload,state", [
    ({"tool_output": '{"exitCode":0,"stdout":"ok"}'}, "passed"),
    ({"tool_output": {"exitCode": 1, "stdout": "failed"}}, "failed"),
    ({"tool_output": "All tests passed"}, "unknown"),
    ({"tool_output": '{"exitCode":'}, "unknown"),
    ({"tool_output": {"exitCode": 0}, "failure_type": "timeout"}, "interrupted"),
    ({"error_message": "permission denied", "failure_type": "permission_denied"}, "unknown"),
    ({"tool_output": {"exitCode": 1}, "is_interrupt": True}, "interrupted"),
])
def test_cursor_outcomes(payload, state):
    assert adapter().outcome(payload).state == state


def test_cursor_post_tool_normalizes_json_result(tmp_path):
    event = adapter().normalize("postToolUse", {"cwd": str(tmp_path), "tool_name": "Shell",
        "tool_input": {"command": "npm run ci"}, "tool_output": '{"exitCode":0,"stdout":"ok"}'})
    assert event.payload["tool_response"] == {"stdout": "ok", "exit_code": 0}


def test_cursor_responses_use_native_fields():
    host = adapter()
    assert host.render("stop", [], 2, "retry") == {"followup_message": "retry"}
    assert host.render("postToolUse", [{"additionalContext": "seen"}], 0, "") == {"additional_context": "seen"}
    assert host.render("sessionStart", [{"additionalContext": "active"}], 0, "") == {"additional_context": "active"}
    result = host.render("preToolUse", [{"permissionDecision": "ask", "permissionDecisionReason": "review"}], 0, "")
    assert result["permission"] == "deny" and "review" in result["user_message"]
    assert host.render("stop", [{"systemMessage": "VERIFIED"}], 0, "") == {}


def test_cursor_bridge_dispatches_native_completion(tmp_path, monkeypatch):
    from core.hosts.bridge import run
    from core import hook
    monkeypatch.setattr(hook, "on_stop", lambda p, r: hook.transport.block("retry"))
    assert run("cursor", "stop", {"cwd": str(tmp_path), "status": "completed"}) == ({"followup_message": "retry"}, 0)


@pytest.mark.parametrize("status", ["aborted", "error"])
def test_cursor_cancelled_stop_does_not_run_verification(tmp_path, monkeypatch, status):
    from core.hosts.bridge import run
    from core import hook
    monkeypatch.setattr(hook, "on_stop", lambda *a: pytest.fail("cancelled session verified"))
    assert run("cursor", "stop", {"cwd": str(tmp_path), "status": status}) == ({}, 0)


def test_cursor_rejects_cwd_outside_declared_workspaces(tmp_path):
    child = tmp_path / "project"
    child.mkdir()
    with pytest.raises(ValueError, match="workspace"):
        adapter().normalize("sessionStart", {"workspace_roots": [str(child)], "cwd": str(tmp_path)})


def test_late_cursor_startup_cannot_overwrite_new_task(tmp_path, monkeypatch):
    from core.hosts.bridge import run
    from core.ledger import Ledger
    from core import evidence
    old = Ledger(root=tmp_path, task="old", request="old")
    old.save()
    scan = evidence.scan_sources
    def racing_scan(root):
        Ledger(root=root, task="new", request="new").save()
        return scan(root)
    monkeypatch.setattr(evidence, "scan_sources", racing_scan)
    run("cursor", "sessionStart", {"cwd": str(tmp_path), "conversation_id": "s"})
    assert Ledger.load(tmp_path).task == "new"
