"""GitHub Copilot CLI native camelCase hooks, independent of VS Code/cloud."""
import json
from .contract import Event, Outcome, event_of, explicit_outcome
from .transport import fields_of

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
    phase = EVENTS[event]
    if event == "agentStop" and payload.get("stopReason", "end_turn") != "end_turn":
        phase = "Cancelled"
    return event_of(phase, clean)


def outcome(payload: dict) -> Outcome:
    raw = payload.get("toolResult")
    if isinstance(raw, dict):
        raw = {**raw, "output": raw.get("textResultForLlm", "")}
    return explicit_outcome(raw, interrupted=payload.get("is_interrupt") is True)


def render(event: str, messages: list[dict], code: int, error: str) -> dict:
    fields = fields_of(messages)
    if event == "agentStop":
        return {"decision": "block", "reason": error} if code == 2 else {"decision": "allow"}
    if event == "preToolUse":
        return {k: fields[k] for k in ("permissionDecision", "permissionDecisionReason") if k in fields}
    if event in {"sessionStart", "postToolUse"} and fields.get("additionalContext"):
        return {"additionalContext": fields["additionalContext"]}
    return {}


LIMITS = (
    "Evidence: tool transport success alone is incomplete; a process exit code or runner receipt is required.",
    "Reports: normal agentStop has no report field; use the status command for the final report.",
    "Prompt hook: Copilot CLI ignores additional prompt context; session/tool context remains available.",
    "Retries: shared completion budget bounds continuation requests.",
)
