"""A record of the moments the runtime could not understand its host.

Three defects in this project were the same defect: a piece wired to something
that never arrived, failing by doing nothing. Nothing is invisible, so each one
survived until somebody thought to look. The general antidote is not more care;
it is making silence leave a trace.

Whenever the runtime is handed something it cannot read, it appends a line here
and `ep-doctor` reports it. A host that renames a field or moves an event then
shows up as a diagnosable symptom instead of a tool that quietly stopped
working.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

FILE = "blindspots.jsonl"
LIMIT = 200


def record(root: Path, kind: str, detail: str) -> None:
    path = root / ".elevenpowers" / FILE
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        lines.append(json.dumps({"kind": kind, "detail": detail[:300], "at": time.time()}))
        path.write_text("\n".join(lines[-LIMIT:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def read(root: Path) -> list[dict]:
    path = root / ".elevenpowers" / FILE
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out
