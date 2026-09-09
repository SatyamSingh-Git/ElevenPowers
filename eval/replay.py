"""Replay real sessions through the runtime and measure what it sees.

Usage:
    python -m eval.replay                     # newest transcript for this project
    python -m eval.replay --all               # every transcript found
    python -m eval.replay --session PATH.jsonl
    python -m eval.replay --verbose

Three of the four numbers here need no labels from me, which is the point. The
host records whether each command failed, so the ground truth for "did the
runtime read this result correctly" comes from the session itself rather than
from the person whose code is being graded.

What this cannot measure is freshness. The working tree as it stood at each
moment is not recoverable from a transcript, so evidence is parsed against a
scratch directory and staleness results would be meaningless. The gate summary
at the end is reported for shape, not as a score.
"""

from __future__ import annotations

import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from core import parsers
from core.claims import infer
from core.evidence import Kind, Result
from core.ledger import Ledger
from core.obligations import risk_of
from core.parsers import parse
from core.payload import read_result
from core.wiring import COMMAND_TOOLS, FILE_TOOLS

from .transcript import Turn, default_dir, load, sessions

# Freshness is not measurable from a transcript, so the working-tree fingerprint
# is pure cost here: two git subprocesses per command, tens of thousands of
# times. In production each command gets its own hook process and pays it once.
parsers.vcs_state = lambda root: ""


def read_result_v0(payload: dict):
    """The reader this replaced, kept as the arm to compare against.

    It assumed a `tool_response` object carrying an `exit_code`. The host sends
    neither: success is an object with no code, and failure is a bare string.
    Both defaults land on zero, so everything read as passing.
    """
    response = payload.get("tool_response", {}) or {}
    output = response if isinstance(response, str) else (
        response.get("stdout", "") + response.get("stderr", "")
    )
    exit_code = 0 if isinstance(response, str) else int(response.get("exit_code", 0) or 0)
    return output, exit_code


@dataclass
class Tally:
    turns: int = 0
    commands: int = 0
    failed_commands: int = 0
    readable: int = 0
    parsed: int = 0
    shapes: Counter = None
    unparsed: Counter = None
    statuses: Counter = None
    claims: Counter = None
    # (reader, "failure" | "success") -> commands scored, and of those, right.
    seen: Counter = None
    right: Counter = None

    def __post_init__(self):
        self.shapes = Counter()
        self.unparsed = Counter()
        self.statuses = Counter()
        self.claims = Counter()
        self.seen = Counter()
        self.right = Counter()


def head(command: str) -> str:
    """The part of a command worth grouping by when reporting what was missed."""
    words = [w for w in parsers._bare(command).split() if not w.startswith("-")]
    return " ".join(words[:2]) if words else "(empty)"


def replay(turns: list[Turn], root: Path, tally: Tally, verbose: bool = False) -> None:
    for turn in turns:
        tally.turns += 1
        ledger = Ledger(root=root)
        ledger.request = turn.prompt
        ledger.claims = infer(turn.prompt) if turn.prompt else []
        for claim in ledger.claims:
            tally.claims[claim.value] += 1

        edited = [
            (call.args.get("file_path") or "")
            for call in turn.calls
            if call.name in FILE_TOOLS and call.name != "Read"
        ]
        ledger.touched = [p for p in edited if p]
        ledger.risk, ledger.domains = risk_of(ledger.touched, turn.prompt)

        clock = 0.0
        for call in turn.calls:
            if call.name not in COMMAND_TOOLS:
                continue
            clock += 1.0
            tally.commands += 1
            payload = call.payload(str(root))
            tally.shapes[_shape(call)] += 1
            if call.failed:
                tally.failed_commands += 1

            result = read_result(payload)
            if result.skip:
                continue
            if result.readable:
                tally.readable += 1

            command = call.args.get("command", "")
            records = parse(command, result.output, result.exit_code, root)
            if records:
                tally.parsed += 1
                _score(records, call.failed, tally, "verdict")
                for record in records:
                    record.at = clock
                ledger.add(records)
            else:
                tally.unparsed[head(command)] += 1

            v0_output, v0_code = read_result_v0(payload)
            v0_records = parse(command, v0_output, v0_code, root)
            if v0_records:
                _score(v0_records, call.failed, tally, "v0")

            if verbose and records and (records[-1].result is Result.PASS) == call.failed:
                print(f"  mismatch: {head(command):<24} host={'fail' if call.failed else 'pass'} "
                      f"read={records[-1].result.value}")

        status = ledger.settle(turn.last_message)
        tally.statuses[status.value] += 1


def _shape(call) -> str:
    if isinstance(call.result, str):
        return "string (failure)"
    if isinstance(call.result, dict):
        keys = set(call.result)
        if "exit_code" in keys or "exitCode" in keys:
            return "object with exit code"
        if keys & {"stdout", "stderr"}:
            return "object, stdout/stderr, no exit code"
        return "object, other keys"
    return "none"


def _score(records, host_failed: bool, tally: Tally, arm: str) -> None:
    """Did the reader agree with the host about whether the command failed?

    The last record is the command-level one: for pytest the per-test records
    come from the printed lines and can legitimately disagree with the exit
    status, so comparing those against a command-level truth would be unfair to
    both readers.

    Scored separately for failing and succeeding commands. A corpus that is 97
    percent successes makes overall accuracy meaningless: a reader that says
    "passed" to everything scores 97 percent while being wrong about the only
    thing the gate needs to know.
    """
    if records[-1].kind is Kind.STABILITY:
        # A repeat run reports on the command it repeated, not on the shell that
        # launched it, so the host's exit status is not the truth for it.
        return
    bucket = "failure" if host_failed else "success"
    tally.seen[(arm, bucket)] += 1
    if (records[-1].result is not Result.PASS) == host_failed:
        tally.right[(arm, bucket)] += 1


def pick(argv: list[str]) -> list[Path]:
    if "--session" in argv:
        return [Path(argv[argv.index("--session") + 1])]
    base = Path(argv[argv.index("--dir") + 1]) if "--dir" in argv else default_dir()
    if not base.exists():
        return []
    found = [p for project in sorted(base.iterdir()) if project.is_dir()
             for p in sessions(project)]
    if not found:
        return []
    return found if "--all" in argv else [found[0]]


def main(argv: list[str]) -> int:
    paths = pick(argv)
    if not paths:
        print("no transcripts found; pass --session PATH.jsonl or --dir DIR")
        return 1

    verbose = "--verbose" in argv
    tally = Tally()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for path in paths:
            turns = load(path)
            if verbose:
                print(f"{path.name}: {len(turns)} turns")
            replay(turns, root, tally, verbose)

    print(f"sessions           {len(paths)}")
    print(f"turns              {tally.turns}")
    print(f"commands           {tally.commands}  ({tally.failed_commands} failed, "
          f"per the host)")
    for shape, count in tally.shapes.most_common():
        print(f"  {shape:<34} {count}")
    print(f"readable results   {_pct(tally.readable, tally.commands)}")
    print(f"parsed to evidence {_pct(tally.parsed, tally.commands)}")

    print()
    print("agreement with the host about whether a command failed")
    print(f"  {'reader':<18}{'failing commands':<22}succeeding commands")
    for arm, label in (("verdict", "this one"), ("v0", "previous")):
        fail = _pct(tally.right[(arm, "failure")], tally.seen[(arm, "failure")])
        good = _pct(tally.right[(arm, "success")], tally.seen[(arm, "success")])
        print(f"  {label:<18}{fail:<22}{good}")
    print()
    print("claims inferred    " + ", ".join(f"{k}={v}" for k, v in tally.claims.most_common()))
    print("gate would report  " + ", ".join(f"{k}={v}" for k, v in tally.statuses.most_common())
          + "   (shape only: freshness is not recoverable from a transcript)")
    if tally.unparsed:
        print()
        print("commands that produced no evidence, most common first:")
        for command, count in tally.unparsed.most_common(12):
            print(f"  {count:>4}  {command}")
    return 0


def _pct(part: int, whole: int) -> str:
    return f"{part}/{whole} ({part / whole:.0%})" if whole else "0/0 (n/a)"


if __name__ == "__main__":
    sys.exit(main(sys.argv))
