"""Cursor Agent hooks; desktop contract, not an implicit CLI compatibility claim."""
from .contract import Event, event_of

EVENTS = {"sessionStart": "SessionStart", "beforeSubmitPrompt": "UserPromptSubmit",
          "preToolUse": "PreToolUse", "postToolUse": "PostToolUse",
          "postToolUseFailure": "PostToolUseFailure", "stop": "Stop"}


def normalize(event: str, payload: dict) -> Event:
    if event not in EVENTS:
        raise ValueError(f"unsupported Cursor event: {event}")
    clean = dict(payload)
    if not clean.get("cwd"):
        roots = payload.get("workspace_roots")
        if not isinstance(roots, list) or len(roots) != 1:
            raise ValueError("Cursor project root is missing or ambiguous")
        clean["cwd"] = roots[0]
    clean["session_id"] = payload.get("conversation_id") or payload.get("session_id", "")
    clean["turn_id"] = payload.get("generation_id", "")
    if clean.get("tool_name") == "Shell":
        clean["tool_name"] = "Bash"
    return event_of(EVENTS[event], clean)
