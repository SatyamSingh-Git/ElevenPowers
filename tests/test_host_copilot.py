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
