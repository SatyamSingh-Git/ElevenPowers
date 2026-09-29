"""GitHub Copilot CLI native camelCase hooks, independent of VS Code/cloud."""
import json
from .contract import Event, Outcome, event_of, explicit_outcome

EVENTS = {"sessionStart": "SessionStart", "userPromptSubmitted": "UserPromptSubmit",
          "preToolUse": "PreToolUse", "postToolUse": "PostToolUse",
          "postToolUseFailure": "PostToolUseFailure", "agentStop": "Stop"}
TOOLS = {"bash": "Bash", "powershell": "PowerShell", "view": "Read", "create": "Write",
         "edit": "Edit", "str_replace_editor": "Edit", "apply_patch": "Patch"}


def normalize(event: str, payload: dict) -> Event:
    if event not in EVENTS:
        raise ValueError(f"unsupported Copilot CLI event: {event}")
    clean = dict(payload)
    clean["session_id"] = payload.get("sessionId", "")
    name = payload.get("toolName", "")
    clean["tool_name"] = TOOLS.get(name, name)
    inputs = payload.get("toolArgs", {})
    if isinstance(inputs, str):
        inputs = json.loads(inputs)
    if not isinstance(inputs, dict):
        raise ValueError("Copilot toolArgs must be an object or JSON object string")
    clean["tool_input"] = inputs
    if event in {"postToolUse", "postToolUseFailure"} and clean["tool_name"] in {"Bash", "PowerShell"}:
        clean["tool_response"] = outcome(payload).result()
    return event_of(EVENTS[event], clean)


def outcome(payload: dict) -> Outcome:
    raw = payload.get("toolResult")
    if isinstance(raw, dict):
        raw = {**raw, "output": raw.get("textResultForLlm", "")}
    return explicit_outcome(raw, interrupted=payload.get("is_interrupt") is True)
