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
    return Event(phase, clean, root)
