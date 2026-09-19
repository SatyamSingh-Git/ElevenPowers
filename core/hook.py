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
from .atlas import neighbourhood
from .claims import infer, opens_new_task
from .evidence import Result
from .ledger import STATE_DIR, Ledger, Status
from .obligations import risk_of
from .parsers import claims_to_run_tests, looks_like_tap, parse, written_paths
from .payload import command_of, read_result, target_file
from .scope import normalise, unrelated
from .verify import discharge
from .report import end_report, gate_message, guidance, start_banner
from .ratchet import snapshot
from .stress import base_commit, confirm, stress, wording
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
        # A task opens at the prompt, whether or not a claim was inferred from
        # it. `Ledger.open_by_edit` can attach a claim later, at the first edit,
        # and until 2026-09-16 that ledger carried no base commit at all -
        # nothing to compare the change against, so the whole discrimination
        # check silently never ran. It cost 37% of a paid sweep: six of sixteen
        # runs, and every one of the six was opened by an edit.
        if request != ledger.request or not ledger.base:
            ledger.base = base_commit(root)
            ledger.opened_dirty = _changed_paths(root)
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
        ledger = Ledger(root=root, task=f"t-{time.time_ns()}", base=base_commit(root),
                        opened_dirty=_changed_paths(root))
    ledger.request = request
    ledger.claims = claims
    ledger.touched = _since_task_opened(ledger, root)
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
        if not target:
            return 0
        here = normalise(target, root)
        # The architecture, at the one moment it can change the edit. Once per
        # file: a neighbourhood note on every edit is one nobody reads.
        #
        # Gated on `briefed`, not on `seen`. `seen` records reads too, and an
        # agent reads a file before editing it practically always - so the note
        # meant for the first edit was suppressed by the read that preceded it,
        # every time, and only a direct blind edit ever saw one.
        brief = neighbourhood(root, here) if here not in ledger.briefed else ""
        if brief:
            ledger.briefed.append(here)
            ledger.save()
        if not ledger.claims:
            if brief:
                _emit("PreToolUse", additionalContext=brief)
            return 0
        drift = unrelated(
            here, ledger.seen, ledger.request, exists=Path(target).exists(),
        )
        if drift:
            ledger.note("scope question", drift)
            ledger.save()
            # One JSON object per hook call, so the brief rides along with the
            # decision rather than being printed after it and discarded.
            extra = {"additionalContext": brief} if brief else {}
            _emit("PreToolUse", permissionDecision="ask",
                  permissionDecisionReason=drift, **extra)
        elif brief:
            _emit("PreToolUse", additionalContext=brief)
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

    # Capture what the command printed BEFORE deciding whether it was evidence.
    #
    # These are different questions and were answered by one `return`. Output
    # was kept only when the parsers recognised a test runner, so
    # `core/assumptions.py` - which asks whether a pattern this task wrote ever
    # matched anything the task actually saw - could only ever see test-runner
    # output. An audit ran `node -e "console.log(...)"`, the textbook case of
    # running a producer to check its shape, and nothing was captured at all.
    #
    # Only when a task is already open: no task means no state to add to, and
    # this must not create a ledger for a command nobody asked about.
    if not records and not written:
        if (root / STATE_DIR / "ledger.json").exists() and result.output.strip():
            watching = Ledger.load(root)
            if watching.task:
                watching.saw_output(command, result.output)
                watching.save()
        # A test command this runtime cannot read is the failure that hides
        # itself: no evidence, no complaint, and under `strict` a refused stop
        # on work that was genuinely tested. Measured on a real repository -
        # three of four packages ran `node --test` and produced nothing, and it
        # took reading the parsers to find out. Now it is in blindspots.jsonl,
        # where `ep_status` and `ep_doctor` already look.
        if claims_to_run_tests(command):
            blindspots.record(root, "unreadable test output",
                              f"{command.strip()[:120]} -> exit {result.exit_code}, "
                              f"no runner recognised")
        elif looks_like_tap(result.output):
            # TAP that no command claims. It used to be read at its word, on the
            # reasoning that a `TAP version 13` header is a self-declaration -
            # until an audit pointed `cat fixture.tap` at it and got a counted
            # passing suite out of a file read. The declaration is in the file,
            # not in the run, and nothing here can tell those apart. So: no
            # record, but not silence either, because a real `bash ci.sh` that
            # emits TAP deserves to find out why it produced nothing.
            blindspots.record(root, "TAP output from a command that claims no tests",
                              f"{command.strip()[:120]} -> looks like TAP; name the "
                              f"runner in .elevenpowers/config.json to have it counted")
        return 0

    ledger = Ledger.load(root)
    # Kept so `core/assumptions.py` can ask whether a pattern this task wrote
    # ever matched anything it actually saw. Bounded, and local only.
    ledger.saw_output(command, result.output)
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
    # Ask the working tree BEFORE concluding there is nothing to gate. Tool
    # events are a proxy for what changed, and agents write through the shell:
    # measured on B4, `jinja2-0cd69481` shipped a 5,396-line patch graded
    # resolved with no Read, Edit or Write event ever reaching the runtime -
    # it used `printf` and redirection - so no claim opened and this function
    # returned on its first line. Two of sixteen runs bypassed the gate that
    # way. Enumerating shell write syntax is a race nobody wins; git already
    # knows, and was being consulted one line too late.
    changed = _since_task_opened(ledger, root)
    for path in changed:
        ledger.observe_edit(path)
    if not ledger.claims:
        return 0

    ledger.touched = sorted(set(ledger.touched) | set(changed))
    status = ledger.settle(payload.get("last_assistant_message", ""))

    if status is not Status.VERIFIED and ledger.config.speaks:
        # Compute what is missing rather than demanding it. Blocking to make the
        # agent run a command costs another turn; running it costs seconds.
        found = discharge(ledger)
        if found:
            ledger.add(found)
            status = ledger.status()

    # PLAN 5.0, pointed at the product: a declared check that already passed
    # before this task began is not evidence the change works. Asked once per
    # task and cached, and it never alters the verdict - 5.12 says detection and
    # intervention are separately justified, and this project blocked 75 percent
    # of runs once already on a signal it had not measured.
    if not ledger.config.verifies:
        # `off` records what it is handed and does nothing of its own. This
        # return used to sit below the block, so the passive profile built a
        # worktree and ran the declared suite in it before going quiet.
        ledger.save()
        return 0

    ledger.discrimination, ledger.failed_before = stress(ledger)
    # And the other half of 5.13, asked rather than waited for. The tests just
    # found red on the base tree are run against the tree as it is now, so a
    # reproduction can be established BY NAME instead of resting on the same
    # base-tree run that decided discrimination. Measured: the targeted path
    # supplied 0 of 7 reproductions before this, because it waited for a passing
    # record carrying a node id and `pytest -q` prints passes as dots.
    proved = confirm(ledger)
    if proved:
        ledger.add(proved)
        status = ledger.status()
    # The best state this task ever proved, kept in a private ref so a later
    # edit cannot lose it. 5.6: a long attempt ends at its latest patch, not its
    # best, and 60-69% of agent failures reach the right code and then damage
    # it. Cheap because it is a `commit-tree`, not a test run.
    # `ledger.status()`, not `status`. They differ on purpose: `settle` returns
    # VERIFIED for a *question* so the turn may end without a claim being
    # discharged, and that permission was being read here as proof of a tree. An
    # audit ended a turn with "Which behavior do you want?" on an UNVERIFIED
    # claim with zero evidence and got a checkpoint noted "the declared checks
    # passed here". Permission to stop and a proven candidate are two decisions;
    # only the second may write a checkpoint.
    if ledger.status() is Status.VERIFIED:
        snapshot(root, ledger.task, "the declared checks passed here")
    ledger.save()

    if not ledger.config.speaks:
        return 0
    if status is Status.VERIFIED:
        _emit("Stop", systemMessage=end_report(ledger))
        return 0

    # Which obligation was unmet, not merely that something was. Every block so
    # far recorded only the status, so nothing could say whether the gate kept
    # firing for the same reason.
    unmet = ", ".join(sorted({c.obligation.key for v in ledger.verdicts() for c in v.missing}))
    detail = f"{status.value}: {unmet or 'stale evidence'}"

    if not ledger.config.blocks:
        ledger.note("gate reported", detail)
        ledger.save()
        _emit("Stop", systemMessage=end_report(ledger))
        return 0

    if ledger.blocks >= MAX_BLOCKS:
        ledger.note("gate gave up", f"{detail} after {ledger.blocks} blocks")
        ledger.save()
        _emit("Stop", systemMessage=end_report(ledger) + "\n\nReported as UNVERIFIED to the user.")
        return 0

    ledger.blocks += 1
    ledger.note("gate blocked", detail)
    ledger.save()
    print(gate_message(ledger), file=sys.stderr)
    return 2


def _since_task_opened(ledger: Ledger, root: Path) -> list[str]:
    """What changed since this task opened, not what was already in flight.

    A real repository is never clean. Attributing every uncommitted file to
    whatever the developer asks next raised the risk tier, demanded obligations
    for untouched code, and handed `core/radius.py` a blast radius computed from
    somebody else's half-finished work: measured on a probe, a task that edited
    one file was credited with four.

    A file that was already dirty and the task then edits is still attributed,
    but not by this function: `Ledger.observe_edit` puts watched edits straight
    into `touched` when the tool event arrives, and Stop unions the two. A
    carve-out for it was written here and a probe proved it did nothing, so it
    was removed rather than left looking load-bearing.

    **The known gap, stated rather than discovered later.** A file that was
    already dirty *and* is edited only through the shell - no tool event - is
    not attributed. That is a narrower miss than the over-attribution it
    replaces, and `blindspots.jsonl` is where the shell-write problem is
    already visible.
    """
    before = set(ledger.opened_dirty)
    return [p for p in _changed_paths(root) if p not in before]


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
                ["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return done.stdout if done.returncode == 0 else None

    toplevel = git("rev-parse", "--show-toplevel")
    if toplevel is None or Path(toplevel.strip()).resolve() != root.resolve():
        return []

    out = git("status", "--porcelain") or ""
    paths = [line[3:].strip().replace("\\", "/").rstrip("/")
             for line in out.splitlines() if line.strip()]
    # The runtime's own ledger is not the task's work. It was already scoring
    # risk as though it were, and once `on_stop` began opening claims from the
    # working tree it would have opened one on a session that changed nothing
    # else - which a probe caught before this shipped.
    return [p for p in paths if p != STATE_DIR and not p.startswith(STATE_DIR + "/")]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
