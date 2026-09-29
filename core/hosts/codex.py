"""Codex hook contract. See https://learn.chatgpt.com/docs/hooks.

Schema examples are not claimed as installed-session captures. apply_patch is
left as a patch event: Git observes its actual edited paths at completion.
"""
from .contract import Event, event_of

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
    return event_of(EVENTS[event], clean)
