"""A self-check for the layer between this runtime and its host.

Three defects in this project lived in that layer, and all three were invisible
to a passing test suite, because the tests called the handlers themselves and
the host was the part that was wrong. What was missing was not a better test of
the runtime but any test at all of the join.

So this exercises the join: it feeds the runtime a payload shaped the way a real
host shapes one and checks that a failing command is recognised as failing, that
the subscription in `hooks.json` still covers everything the handlers branch on,
and that nothing unreadable has arrived while the user was working.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import blindspots
from .evidence import Result
from .parsers import parse
from .payload import read_result
from .wiring import RECORDED, rendered

# What a real host sends when `pytest` exits non-zero: a bare string, an exit
# code in the first line, and no structure at all. Captured from a session
# transcript, not invented, because inventing it is what went wrong before.
FAILING_PAYLOAD = {
    "hook_event_name": "PostToolUseFailure",
    "tool_name": "Bash",
    "tool_input": {"command": "python -m pytest tests -q"},
    "tool_result": "Error: Exit code 1\nF...\n1 failed, 2 passed in 0.31s\n",
}
PASSING_PAYLOAD = {
    "hook_event_name": "PostToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "python -m pytest tests -q"},
    "tool_result": {"stdout": "...\n3 passed in 0.29s\n", "stderr": "",
                    "interrupted": False, "isImage": False},
}


class Check:
    def __init__(self, name: str, ok: bool, detail: str = "") -> None:
        self.name, self.ok, self.detail = name, ok, detail

    def line(self) -> str:
        return f"{'ok  ' if self.ok else 'FAIL'}  {self.name}" + (
            f"\n        {self.detail}" if self.detail else ""
        )


def checks(root: Path, plugin: Path | None = None) -> list[Check]:
    out = [
        Check(f"python {sys.version.split()[0]}", sys.version_info >= (3, 11),
              "" if sys.version_info >= (3, 11) else "3.11 or later is required"),
        _reads_failure(root),
        _reads_success(root),
        _subscription(plugin),
        _writable(root),
    ]
    out.append(_blindspots(root))
    return out


def _reads_failure(root: Path) -> Check:
    """The check that would have caught the worst of the three defects."""
    result = read_result(FAILING_PAYLOAD)
    records = parse(FAILING_PAYLOAD["tool_input"]["command"], result.output,
                    result.exit_code, root)
    failing = [r for r in records if r.result is not Result.PASS]
    return Check(
        "a failing command is recorded as failing",
        bool(failing),
        "" if failing else f"exit={result.exit_code} records={len(records)}; "
                           "the host's failure shape is not being recognised",
    )


def _reads_success(root: Path) -> Check:
    result = read_result(PASSING_PAYLOAD)
    records = parse(PASSING_PAYLOAD["tool_input"]["command"], result.output,
                    result.exit_code, root)
    passing = [r for r in records if r.result is Result.PASS]
    return Check("a passing command is recorded as passing", bool(passing),
                 "" if passing else f"exit={result.exit_code} records={len(records)}")


def _subscription(plugin: Path | None) -> Check:
    path = (plugin or Path(__file__).resolve().parents[1] / "plugin") / "hooks" / "hooks.json"
    if not path.exists():
        return Check("hooks.json subscribes to every event the runtime handles",
                     False, f"missing: {path}")
    try:
        found = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return Check("hooks.json subscribes to every event the runtime handles",
                     False, str(exc))
    if found != json.loads(rendered()):
        return Check("hooks.json subscribes to every event the runtime handles", False,
                     "the file has drifted from core/wiring.py; "
                     "run python -m core.wiring to rewrite it")
    return Check(f"hooks.json subscribes to every event the runtime handles "
                 f"({len(RECORDED)} tools recorded)", True)


def _writable(root: Path) -> Check:
    state = root / ".elevenpowers"
    try:
        state.mkdir(parents=True, exist_ok=True)
        probe = state / ".probe"
        probe.write_text("x", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return Check("the ledger directory is writable", False, str(exc))
    return Check(f"the ledger directory is writable ({state})", True)


def _blindspots(root: Path) -> Check:
    found = blindspots.read(root)
    if not found:
        return Check("nothing unreadable has arrived from the host", True)
    kinds = sorted({b.get("kind", "?") for b in found})
    return Check("nothing unreadable has arrived from the host", False,
                 f"{len(found)} record(s): {', '.join(kinds)}; "
                 f"latest: {found[-1].get('detail', '')}")


def report(root: Path, plugin: Path | None = None) -> tuple[str, bool]:
    results = checks(root, plugin)
    body = "\n".join(c.line() for c in results)
    ok = all(c.ok for c in results)
    tail = "" if ok else "\n\nA failing check means the runtime is not seeing what it needs."
    return f"{body}{tail}", ok
