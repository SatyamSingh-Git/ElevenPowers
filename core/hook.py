"""Claude Code hook entry point.

One process, one event: `python -m core.hook <event>` with the hook payload on
stdin. Output follows the host contract: JSON on stdout for context and
permission decisions, exit 2 to block.

Hook stdout on exit 0 reaches the model only through `hookSpecificOutput`, never
as plain text, so every injection here uses that form.
"""

from __future__ import annotations

import fnmatch
import json
import sys
import time
from pathlib import Path

from .claims import infer
from .evidence import Kind, Result
from .ledger import Ledger, Status
from .obligations import risk_of
from .parsers import parse
from .scope import normalise, unrelated
from .report import end_report, gate_message, start_banner

MAX_BLOCKS = 2
DESTRUCTIVE = (
    "rm -rf /", "rm -rf ~", "git push --force", "git push -f",
    "DROP DATABASE", "DROP TABLE", "mkfs", "dd if=", ":(){",
)


def main(argv: list[str]) -> int:
    event = argv[1] if len(argv) > 1 else ""
    payload = _read_payload()
    root = Path(payload.get("cwd") or Path.cwd())
    if not root.exists():
        return 0

    handler = {
        "SessionStart": on_session_start,
        "UserPromptSubmit": on_prompt,
        "PreToolUse": on_pre_tool,
        "PostToolUse": on_post_tool,
        "Stop": on_stop,
    }.get(event)
    return handler(payload, root) if handler else 0


def _read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _emit(event: str, **fields) -> None:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, **fields}}))


def on_session_start(payload: dict, root: Path) -> int:
    ledger = Ledger.load(root)
    if ledger.claims:
        _emit("SessionStart", additionalContext=start_banner(ledger))
    return 0


def on_prompt(payload: dict, root: Path) -> int:
    request = (payload.get("prompt") or "").strip()
    if not request:
        return 0

    ledger = Ledger.load(root)
    claims = infer(request)
    if not claims:
        ledger.claims = []
        ledger.save()
        return 0

    ledger.task = ledger.task or f"t-{int(time.time())}"
    ledger.request = request
    ledger.claims = claims
    ledger.touched = _changed_paths(root)
    ledger.risk, ledger.domains = risk_of(ledger.touched, request)
    ledger.blocks = 0
    ledger.save()
    _emit("UserPromptSubmit", additionalContext=start_banner(ledger))
    return 0


def on_pre_tool(payload: dict, root: Path) -> int:
    tool = payload.get("tool_name", "")
    args = payload.get("tool_input", {}) or {}
    ledger = Ledger.load(root)

    if tool == "Bash":
        command = args.get("command", "")
        hit = next((d for d in DESTRUCTIVE if d.lower() in command.lower()), None)
        if hit:
            _emit(
                "PreToolUse",
                permissionDecision="ask",
                permissionDecisionReason=f"destructive pattern in command: {hit}",
            )
        return 0

    if tool in ("Edit", "Write", "NotebookEdit"):
        target = args.get("file_path", "")
        if not target or not ledger.claims:
            return 0
        if ledger.allow and not _within(root, target, ledger.allow):
            _emit("PreToolUse", permissionDecision="ask",
                  permissionDecisionReason=(
                      f"{target} is outside the declared scope for this task "
                      f"({', '.join(ledger.allow)})."))
            return 0
        drift = unrelated(
            normalise(target, root), ledger.seen, ledger.request,
            exists=Path(target).exists(),
        )
        if drift:
            ledger.note("scope question", drift)
            ledger.save()
            _emit("PreToolUse", permissionDecision="ask", permissionDecisionReason=drift)
    return 0


FILE_TOOLS = {"Read", "Edit", "Write", "NotebookEdit", "NotebookRead"}


def on_post_tool(payload: dict, root: Path) -> int:
    tool = payload.get("tool_name", "")
    if tool in FILE_TOOLS:
        target = (payload.get("tool_input", {}) or {}).get("file_path", "")
        if target:
            ledger = Ledger.load(root)
            ledger.saw(target)
            ledger.save()
        return 0
    if tool != "Bash":
        return 0
    args = payload.get("tool_input", {}) or {}
    response = payload.get("tool_response", {}) or {}
    command = args.get("command", "")
    output = response if isinstance(response, str) else (
        response.get("stdout", "") + response.get("stderr", "")
    )
    exit_code = 0 if isinstance(response, str) else int(response.get("exit_code", 0) or 0)

    records = parse(command, output, exit_code, root)
    if not records:
        return 0

    ledger = Ledger.load(root)
    ledger.add(records)
    ledger.save()

    failures = [r for r in records if r.result is Result.FAIL]
    if failures and ledger.claims:
        _emit(
            "PostToolUse",
            additionalContext=f"recorded: {len(records)} evidence record(s), {len(failures)} failing",
        )
    return 0


def on_stop(payload: dict, root: Path) -> int:
    ledger = Ledger.load(root)
    if not ledger.claims:
        return 0

    ledger.touched = sorted(set(ledger.touched) | set(_changed_paths(root)))
    status = ledger.settle(payload.get("last_assistant_message", ""))
    ledger.save()
    if status is Status.VERIFIED:
        _emit("Stop", additionalContext=end_report(ledger))
        return 0

    if ledger.blocks >= MAX_BLOCKS:
        ledger.note("gate gave up", f"{status.value} after {ledger.blocks} blocks")
        ledger.save()
        _emit("Stop", additionalContext=end_report(ledger) + "\n\nReported as UNVERIFIED to the user.")
        return 0

    ledger.blocks += 1
    ledger.note("gate blocked", status.value)
    ledger.save()
    print(gate_message(ledger), file=sys.stderr)
    return 2


def _within(root: Path, target: str, patterns: list[str]) -> bool:
    try:
        rel = str(Path(target).resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return False
    return any(fnmatch.fnmatch(rel, p) for p in patterns)


def _changed_paths(root: Path) -> list[str]:
    """Paths this task has already touched, or an empty list.

    `git status` walks up the directory tree, so a directory that is not itself
    a repository would otherwise report an unrelated parent's changes and score
    the wrong risk tier. The toplevel check keeps that from happening.
    """
    import subprocess

    def git(*args: str) -> str | None:
        try:
            done = subprocess.run(
                ["git", *args], cwd=root, capture_output=True, text=True, timeout=5
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return done.stdout if done.returncode == 0 else None

    toplevel = git("rev-parse", "--show-toplevel")
    if toplevel is None or Path(toplevel.strip()).resolve() != root.resolve():
        return []

    out = git("status", "--porcelain") or ""
    return [line[3:].strip().replace("\\", "/") for line in out.splitlines() if line.strip()]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
