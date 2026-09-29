"""Explicit host boundaries: no implicit project or successful exit status."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Event:
    phase: str
    payload: dict
    root: Path


@dataclass(frozen=True)
class Outcome:
    output: str = ""
    exit_code: int | None = None
    state: str = "unknown"

    def result(self) -> dict:
        """Legacy engine envelope; incomplete must never fall through to exit 0."""
        if self.state not in {"passed", "failed"}:
            return {"stdout": self.output, "interrupted": True}
        return {"stdout": self.output, "exit_code": self.exit_code}


def root_of(payload: dict) -> Path:
    value = payload.get("cwd")
    if not isinstance(value, str) or not value:
        raise ValueError("host event has no explicit project root")
    root = Path(value)
    if not root.is_absolute() or not root.is_dir():
        raise ValueError("host project root must be an existing absolute directory")
    return root.resolve()


def event_of(phase: str, payload: dict) -> Event:
    root = root_of(payload)
    clean = dict(payload)
    clean["cwd"] = str(root)
    clean["hook_event_name"] = phase
    inputs = clean.get("tool_input") or {}
    if not isinstance(inputs, dict):
        raise ValueError("tool input must be an object")
    if phase in {"PostToolUse", "PostToolUseFailure"}:
        where = next((inputs[k] for k in ("workdir", "cwd", "working_directory") if inputs.get(k)), None)
        if where:
            if not isinstance(where, str):
                raise ValueError("tool working directory must be a string")
            directory = Path(where)
            directory = directory if directory.is_absolute() else root / directory
            if directory.resolve() != root:
                clean["tool_response"] = Outcome(state="unknown").result()
    return Event(phase, clean, root)


def explicit_outcome(raw: object, *, interrupted: bool = False) -> Outcome:
    """Read structured exit status, never prose that could come from the command."""
    if not isinstance(raw, dict):
        return Outcome(raw if isinstance(raw, str) else "", state="interrupted" if interrupted else "unknown")
    output = "\n".join(raw[k] for k in ("stdout", "stderr", "output")
                       if isinstance(raw.get(k), str))
    if interrupted or any(raw.get(k) is True for k in ("interrupted", "timed_out", "timeout", "cancelled", "aborted")):
        return Outcome(output, state="interrupted")
    code = next((raw[k] for k in ("exit_code", "exitCode", "returncode") if k in raw), None)
    if type(code) is int:
        return Outcome(output, code, "passed" if code == 0 else "failed")
    if raw.get("session_id") is not None:
        return Outcome(output, state="running")
    return Outcome(output)
