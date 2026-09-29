"""Cursor Agent hooks; desktop contract, not an implicit CLI compatibility claim."""
import json
from pathlib import Path
from .contract import Event, Outcome, event_of, explicit_outcome
from .transport import fields_of

EVENTS = {"sessionStart": "SessionStart", "beforeSubmitPrompt": "UserPromptSubmit",
          "preToolUse": "PreToolUse", "postToolUse": "PostToolUse",
          "postToolUseFailure": "PostToolUseFailure", "stop": "Stop"}
LIMITS = (
    "Ambiguous multi-root events require explicit cwd; no first-root fallback.",
    "Stop has no ordinary report field; inspect the persisted verdict with the status command.",
    "Native preToolUse approval asks are not enforced; questioned operations receive a denial.",
)


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
    phase = EVENTS[event]
    if event == "stop" and payload.get("status") != "completed":
        phase = "Cancelled"
    normalized = event_of(phase, clean)
    roots = payload.get("workspace_roots")
    if roots is not None:
        if not isinstance(roots, list) or not roots or any(not isinstance(r, str) or not Path(r).is_absolute() for r in roots):
            raise ValueError("invalid Cursor workspace roots")
        if not any(normalized.root.is_relative_to(Path(r).resolve()) for r in roots):
            raise ValueError("Cursor cwd is outside declared workspaces")
    return normalized


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


def render(event: str, messages: list[dict], code: int, error: str) -> dict:
    fields = fields_of(messages)
    result = {}
    if event == "stop":
        return {"followup_message": error} if code == 2 else {}
    if event in {"sessionStart", "postToolUse"} and fields.get("additionalContext"):
        result["additional_context"] = fields["additionalContext"]
    if event == "preToolUse" and fields.get("permissionDecision") in {"ask", "deny"}:
        reason = fields.get("permissionDecisionReason", "Review this operation")
        result.update(permission="deny", user_message=reason,
                      agent_message=reason + ". Review this operation with the user before retrying.")
    return result
