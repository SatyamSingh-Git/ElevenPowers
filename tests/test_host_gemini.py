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


@pytest.mark.parametrize("raw,state", [
    ({"llmContent": "Output: ok", "data": {"exitCode": 0}}, "passed"),
    ({"llmContent": "Output: failed", "data": {"exitCode": 1, "isError": True}}, "failed"),
    ({"llmContent": "all checks passed", "returnDisplay": "ok"}, "unknown"),
    ({"error": {"type": "PATH_NOT_IN_WORKSPACE"}}, "unknown"),
    ({"data": {"exitCode": 0}, "interrupted": True}, "interrupted"),
    ({"llmContent": [{"text": "first"}, {"text": "second"}]}, "unknown"),
])
def test_gemini_status_requires_structured_exit(raw, state):
    assert adapter().outcome({"tool_response": raw}).state == state


def test_gemini_result_content_is_retained(tmp_path):
    event = adapter().normalize("AfterTool", {"cwd": str(tmp_path), "tool_name": "run_shell_command",
        "tool_input": {"command": "npm run ci"}, "tool_response": {"llmContent": "output", "data": {"exitCode": 1}}})
    assert event.payload["tool_response"] == {"stdout": "output", "exit_code": 1}


def test_gemini_native_response_decisions():
    host = adapter()
    assert host.render("AfterAgent", [], 2, "missing") == {"decision": "deny", "reason": "missing"}
    result = host.render("BeforeTool", [{"permissionDecision": "ask", "permissionDecisionReason": "review"}], 0, "")
    assert result["decision"] == "deny"
    assert "review" in result["reason"] and "permissionDecision" not in result
    result = host.render("AfterTool", [{"additionalContext": "observed"}], 0, "")
    assert result == {"hookSpecificOutput": {"hookEventName": "AfterTool", "additionalContext": "observed"}}


def test_gemini_bridge_is_registered(tmp_path, monkeypatch):
    from core.hosts.bridge import run
    from core import hook
    monkeypatch.setattr(hook, "on_stop", lambda p, r: hook.transport.block("retry"))
    assert run("gemini", "AfterAgent", {"cwd": str(tmp_path)}) == ({"decision": "deny", "reason": "retry"}, 0)


def test_gemini_execution_error_and_signal_are_not_reproduced_failures():
    assert adapter().outcome({"tool_response": {"data": {"exitCode": 1}, "error": {"type": "SHELL_EXECUTE_ERROR"}}}).state == "unknown"
    assert adapter().outcome({"tool_response": {"data": {"exitCode": 1, "aborted": True}}}).state == "interrupted"


def test_gemini_native_retry_preserves_task(tmp_path, monkeypatch):
    from core.hosts.bridge import run
    from core import hook
    monkeypatch.setattr(hook, "on_stop", lambda p, r: hook.transport.block("fix the test"))
    run("gemini", "AfterAgent", {"cwd": str(tmp_path), "session_id": "g"})
    monkeypatch.setattr(hook, "on_prompt", lambda *a: pytest.fail("retry opened task"))
    assert run("gemini", "BeforeAgent", {"cwd": str(tmp_path), "session_id": "g", "prompt": "fix the test"}) == ({}, 0)


def test_gemini_background_or_other_directory_cannot_certify_root(tmp_path):
    for inputs in [{"dir_path": "child"}, {"is_background": True}]:
        event = adapter().normalize("AfterTool", {"cwd": str(tmp_path), "tool_name": "run_shell_command",
            "tool_input": {"command": "npm run ci", **inputs}, "tool_response": {"data": {"exitCode": 0}}})
        assert event.payload["tool_response"].get("interrupted") is True
