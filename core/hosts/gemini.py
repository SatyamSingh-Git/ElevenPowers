"""Gemini CLI lifecycle adapter; hook reference at geminicli.com/docs/hooks/."""
from .contract import Event, Outcome, event_of, explicit_outcome

EVENTS = {"SessionStart": "SessionStart", "BeforeAgent": "UserPromptSubmit",
          "BeforeTool": "PreToolUse", "AfterTool": "PostToolUse", "AfterAgent": "Stop"}
TOOLS = {"run_shell_command": "Bash", "read_file": "Read", "write_file": "Write", "replace": "Edit"}


def normalize(event: str, payload: dict) -> Event:
    if event not in EVENTS:
        raise ValueError(f"unsupported Gemini event: {event}")
    clean = dict(payload)
    name = payload.get("tool_name", "")
    clean["tool_name"] = TOOLS.get(name, name)
    if event == "AfterAgent":
        clean["last_assistant_message"] = payload.get("prompt_response") or ""
    if event == "AfterTool" and clean.get("tool_name") == "Bash":
        clean["tool_response"] = outcome(payload).result()
    return event_of(EVENTS[event], clean)


def outcome(payload: dict) -> Outcome:
    raw = payload.get("tool_response")
    if not isinstance(raw, dict):
        return Outcome()
    content = raw.get("llmContent", "")
    if isinstance(content, list):
        content = "\n".join(part.get("text", "") for part in content
                            if isinstance(part, dict) and isinstance(part.get("text"), str))
    data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    result = explicit_outcome({**raw, **data, "output": content if isinstance(content, str) else ""},
                              interrupted=payload.get("is_interrupt") is True)
    # Execution/permission errors without a command status are not test failures.
    if raw.get("error") and result.state == "passed":
        return Outcome(result.output)
    return result
