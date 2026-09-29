"""Codex hook contract. See https://learn.chatgpt.com/docs/hooks.

Schema examples are not claimed as installed-session captures. apply_patch is
left as a patch event: Git observes its actual edited paths at completion.
"""
from .contract import Event, Outcome, event_of, explicit_outcome
from .transport import fields_of

EVENTS = {
    "SessionStart": "SessionStart", "UserPromptSubmit": "UserPromptSubmit",
    "PreToolUse": "PreToolUse", "PostToolUse": "PostToolUse", "Stop": "Stop",
}


def normalize(event: str, payload: dict) -> Event:
    if event not in EVENTS:
        raise ValueError(f"unsupported Codex event: {event}")
    clean = dict(payload)
    if clean.get("tool_name") == "apply_patch":
        clean["tool_name"] = "Patch"
    if event == "PostToolUse" and clean.get("tool_name") == "Bash":
        clean["tool_response"] = outcome(payload).result()
    return event_of(EVENTS[event], clean)


def outcome(payload: dict) -> Outcome:
    return explicit_outcome(payload.get("tool_response"), interrupted=payload.get("is_interrupt") is True)


def render(event: str, messages: list[dict], code: int, error: str) -> dict:
    fields = fields_of(messages)
    result = {}
    if "systemMessage" in fields:
        result["systemMessage"] = fields.pop("systemMessage")
    if event == "Stop":
        if code == 2:
            result.update(decision="block", reason=error)
    elif fields:
        result["hookSpecificOutput"] = {"hookEventName": event, **fields}
    return result
