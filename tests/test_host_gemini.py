"""Gemini CLI documented native contract fixtures, not live captures."""
import pytest


def adapter():
    from core.hosts import gemini
    return gemini


@pytest.mark.parametrize("native,phase", [("SessionStart", "SessionStart"), ("BeforeAgent", "UserPromptSubmit"),
    ("BeforeTool", "PreToolUse"), ("AfterTool", "PostToolUse"), ("AfterAgent", "Stop")])
def test_gemini_native_lifecycle(native, phase, tmp_path):
    event = adapter().normalize(native, {"cwd": str(tmp_path), "prompt": "fix it", "prompt_response": "done"})
    assert event.phase == phase
    if phase == "Stop":
        assert event.payload["last_assistant_message"] == "done"


@pytest.mark.parametrize("native,canonical,key", [("run_shell_command", "Bash", "command"),
    ("read_file", "Read", "file_path"), ("write_file", "Write", "file_path"), ("replace", "Edit", "file_path")])
def test_gemini_tool_names(native, canonical, key, tmp_path):
    event = adapter().normalize("BeforeTool", {"cwd": str(tmp_path), "tool_name": native,
        "tool_input": {"command": "npm run ci", "file_path": "src.py"}})
    assert event.payload["tool_name"] == canonical
    assert key in event.payload["tool_input"]


def test_gemini_missing_root_is_not_the_plugin_directory():
    with pytest.raises(ValueError, match="root"):
        adapter().normalize("SessionStart", {})
