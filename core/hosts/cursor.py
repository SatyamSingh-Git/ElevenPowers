"""Cursor Agent hooks; desktop contract, not an implicit CLI compatibility claim."""
import json
from .contract import Event, Outcome, event_of, explicit_outcome

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
    if event in {"postToolUse", "postToolUseFailure"} and clean.get("tool_name") == "Bash":
        clean["tool_response"] = outcome(payload).result()
    return event_of(EVENTS[event], clean)


def outcome(payload: dict) -> Outcome:
    raw = payload.get("tool_output")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            pass
    interrupted = payload.get("is_interrupt") is True or payload.get("failure_type") == "timeout"
    if payload.get("failure_type") == "permission_denied":
        return Outcome(str(payload.get("error_message") or ""))
    return explicit_outcome(raw, interrupted=interrupted)
