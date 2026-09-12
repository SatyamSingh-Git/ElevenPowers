"""Claude Code hook entry point.

One process, one event: `python -m core.hook <event>` with the hook payload on
stdin. Output follows the host contract: JSON on stdout for context and
permission decisions, exit 2 to block.

Hook stdout on exit 0 reaches the model only through `hookSpecificOutput`, never
as plain text, so every injection here uses that form.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from . import blindspots
from .claims import infer, opens_new_task
from .evidence import Result
from .ledger import Ledger, Status
from .obligations import risk_of
from .parsers import parse, written_paths
from .payload import command_of, read_result, target_file
from .scope import normalise, unrelated
from .verify import discharge
from .report import end_report, gate_message, guidance, start_banner
from .wiring import COMMAND_TOOLS, EDIT_TOOLS, FILE_TOOLS

MAX_BLOCKS = 2
DESTRUCTIVE = (
    "rm -rf /", "rm -rf ~", "git push --force", "git push -f",
    "DROP DATABASE", "DROP TABLE", "mkfs", "dd if=", ":(){",
)


HANDLERS = {
    "SessionStart": "on_session_start",
    "UserPromptSubmit": "on_prompt",
    "PreToolUse": "on_pre_tool",
    "PostToolUse": "on_post_tool",
    "PostToolUseFailure": "on_post_tool",
    "Stop": "on_stop",
}


def main(argv: list[str]) -> int:
    event = argv[1] if len(argv) > 1 else ""
    payload = _read_payload()
    root = Path(payload.get("cwd") or Path.cwd())
    if not root.exists():
        return 0

    name = HANDLERS.get(event)
    if not name:
        return 0
    # The event name carries information the payload does not: a failing tool
    # call arrives under a different event, and that is often the only signal
    # that it failed.
    payload.setdefault("hook_event_name", event)
    return globals()[name](payload, root)


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
        if ledger.claims and not opens_new_task(request):
            return 0        # a continuation keeps the obligations already open
        ledger.claims = []
        ledger.request = request
        ledger.save()
        return 0

    if request != ledger.request:
        # A prompt that states its own subject starts a task, and a task starts
        # empty. Keeping the id meant the new request inherited the previous
        # one's evidence, read set and guided flag — so a suite run for the last
        # bug could discharge an obligation for this one, purely because the
        # ledger happened to still be sitting in the same directory.
        ledger = Ledger(root=root, task=f"t-{time.time_ns()}")
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
    ledger = Ledger.load(root)

    if tool in COMMAND_TOOLS:
        command = command_of(payload)
        hit = next((d for d in DESTRUCTIVE if d.lower() in command.lower()), None)
        if hit:
            _emit(
                "PreToolUse",
                permissionDecision="ask",
                permissionDecisionReason=f"destructive pattern in command: {hit}",
            )
        return 0

    if tool in EDIT_TOOLS:
        target = target_file(payload)
        if not target or not ledger.claims:
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


def on_post_tool(payload: dict, root: Path) -> int:
    tool = payload.get("tool_name", "")
    if tool in FILE_TOOLS:
        target = target_file(payload)
        if target:
            ledger = Ledger.load(root)
            if tool in EDIT_TOOLS:
                ledger.observe_edit(target)
                _guide(ledger)
            else:
                ledger.saw(target)
            ledger.save()
        return 0
    if tool not in COMMAND_TOOLS:
        return 0

    command = command_of(payload)
    result = read_result(payload)
    if result.skip:
        return 0
    if not result.readable:
        blindspots.record(root, "unreadable tool result",
                          f"{tool}: no result field in {sorted(payload)}")
        return 0

    records = parse(command, result.output, result.exit_code, root)
    written = written_paths(command) if result.ok else []
    if not records and not written:
        return 0

    ledger = Ledger.load(root)
    for path in written:
        ledger.observe_edit(path)
    ledger.add(records)
    ledger.save()

    failures = [r for r in records if r.result is Result.FAIL]
    if failures and ledger.claims:
        _emit(
            "PostToolUse",
            additionalContext=f"recorded: {len(records)} evidence record(s), {len(failures)} failing",
        )
    return 0


def _guide(ledger: Ledger) -> None:
    """Say what would prove this work, once, at the edit that opens the claim.

    Measured live, the gate stopped nearly every first attempt to finish, and
    nearly always on work that was already correct: the agent had done the job
    and simply not shown it. The obligations were stated in the opening banner
    and were far behind by the end. This is the same information delivered
    while it can still change what happens.
    """
    if ledger.guided or not ledger.claims or not ledger.config.speaks:
        return
    words = guidance(ledger)
    if not words:
        return
    ledger.guided = True
    _emit("PostToolUse", additionalContext=words)


def on_stop(payload: dict, root: Path) -> int:
    ledger = Ledger.load(root)
    if not ledger.claims:
        return 0

    ledger.touched = sorted(set(ledger.touched) | set(_changed_paths(root)))
    status = ledger.settle(payload.get("last_assistant_message", ""))

    if status is not Status.VERIFIED and ledger.config.speaks:
        # Compute what is missing rather than demanding it. Blocking to make the
        # agent run a command costs another turn; running it costs seconds.
        found = discharge(ledger)
        if found:
            ledger.add(found)
            status = ledger.status()
    ledger.save()

    if not ledger.config.speaks:
        return 0
    if status is Status.VERIFIED:
        _emit("Stop", additionalContext=end_report(ledger))
        return 0

    # Which obligation was unmet, not merely that something was. Every block so
    # far recorded only the status, so nothing could say whether the gate kept
    # firing for the same reason.
    unmet = ", ".join(sorted({c.obligation.key for v in ledger.verdicts() for c in v.missing}))
    detail = f"{status.value}: {unmet or 'stale evidence'}"

    if not ledger.config.blocks:
        ledger.note("gate reported", detail)
        ledger.save()
        _emit("Stop", additionalContext=end_report(ledger))
        return 0

    if ledger.blocks >= MAX_BLOCKS:
        ledger.note("gate gave up", f"{detail} after {ledger.blocks} blocks")
        ledger.save()
        _emit("Stop", additionalContext=end_report(ledger) + "\n\nReported as UNVERIFIED to the user.")
        return 0

    ledger.blocks += 1
    ledger.note("gate blocked", detail)
    ledger.save()
    print(gate_message(ledger), file=sys.stderr)
    return 2


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
