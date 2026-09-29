"""Gemini CLI lifecycle adapter; hook reference at geminicli.com/docs/hooks/."""
from .contract import Event, event_of

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
    return event_of(EVENTS[event], clean)
