"""Native Copilot CLI camelCase hook contracts; no cloud/VS Code claim."""
import json
import pytest


def adapter():
    from core.hosts import copilot
    return copilot


@pytest.mark.parametrize("native,phase", [("sessionStart", "SessionStart"), ("userPromptSubmitted", "UserPromptSubmit"),
    ("preToolUse", "PreToolUse"), ("postToolUse", "PostToolUse"), ("postToolUseFailure", "PostToolUseFailure"), ("agentStop", "Stop")])
def test_copilot_native_event_mapping(native, phase, tmp_path):
    event = adapter().normalize(native, {"cwd": str(tmp_path), "sessionId": "s", "stopReason": "end_turn"})
    assert event.phase == phase and event.payload["session_id"] == "s"
    assert event.payload.get("last_assistant_message", "") == ""


@pytest.mark.parametrize("tool,canonical", [("bash", "Bash"), ("powershell", "PowerShell"), ("view", "Read"), ("create", "Write"), ("edit", "Edit"), ("apply_patch", "Patch")])
def test_copilot_native_tool_names(tool, canonical, tmp_path):
    event = adapter().normalize("preToolUse", {"cwd": str(tmp_path), "toolName": tool,
        "toolArgs": json.dumps({"command": "npm run ci", "path": "app.py"})})
    assert event.payload["tool_name"] == canonical
    assert event.payload["tool_input"]["command"] == "npm run ci"


def test_copilot_malformed_tool_args_rejected(tmp_path):
    with pytest.raises(ValueError):
        adapter().normalize("preToolUse", {"cwd": str(tmp_path), "toolArgs": "invalid"})


@pytest.mark.parametrize("payload,state", [
    ({"toolResult": {"resultType": "success", "textResultForLlm": "all passed"}}, "unknown"),
    ({"toolResult": {"resultType": "success", "exitCode": 0, "textResultForLlm": "ok"}}, "passed"),
    ({"toolResult": {"exitCode": 1, "textResultForLlm": "failed"}}, "failed"),
    ({"error": "permission denied"}, "unknown"),
    ({"is_interrupt": True, "toolResult": {"exitCode": 0}}, "interrupted"),
    ({"toolResult": {"exitCode": False}}, "unknown"),
])
def test_copilot_transport_success_is_not_process_success(payload, state):
    assert adapter().outcome(payload).state == state


def test_copilot_failed_transport_without_status_is_incomplete(tmp_path):
    event = adapter().normalize("postToolUseFailure", {"cwd": str(tmp_path), "toolName": "bash",
        "toolArgs": {"command": "npm run ci"}, "error": "cancelled"})
    assert event.payload["tool_response"].get("interrupted") is True


def test_copilot_native_responses():
    host = adapter()
    assert host.render("agentStop", [], 2, "retry") == {"decision": "block", "reason": "retry"}
    assert host.render("agentStop", [{"systemMessage": "verified"}], 0, "") == {"decision": "allow"}
    assert host.render("sessionStart", [{"additionalContext": "active"}], 0, "") == {"additionalContext": "active"}
    assert host.render("postToolUse", [{"additionalContext": "observed"}], 0, "") == {"additionalContext": "observed"}
    assert host.render("userPromptSubmitted", [{"additionalContext": "claims"}], 0, "") == {}
    result = host.render("preToolUse", [{"permissionDecision": "ask", "permissionDecisionReason": "review"}], 0, "")
    assert result == {"permissionDecision": "ask", "permissionDecisionReason": "review"}


def test_copilot_native_dispatch(tmp_path, monkeypatch):
    from core.hosts.bridge import run
    from core import hook
    monkeypatch.setattr(hook, "on_stop", lambda p, r: hook.transport.block("retry"))
    assert run("copilot", "agentStop", {"cwd": str(tmp_path), "stopReason": "end_turn"}) == ({"decision": "block", "reason": "retry"}, 0)
