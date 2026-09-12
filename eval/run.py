"""Run the labelled scenarios and print the gate's confusion matrix.

Usage: python -m eval.run [--verbose] [--tag TAG]

The gate is a classifier. This measures it as one. False-block rate is the
number that decides whether anyone keeps the tool installed; miss rate is the
number the tool exists to reduce.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from core.claims import infer
from core.evidence import Result
from core.ledger import Ledger, Status
from core.obligations import risk_of
from core.parsers import parse

from .bundle import GIT
from .heldout import HELD_OUT
from .scenarios import SCENARIOS, Act, Scenario


@dataclass
class Outcome:
    scenario: Scenario
    blocked: bool
    status: Status
    detail: str

    @property
    def verdict(self) -> str:
        if self.scenario.complete and self.blocked:
            return "FALSE BLOCK"
        if not self.scenario.complete and not self.blocked:
            return "MISS"
        return "ok"


def build(repo: dict[str, str], root: Path) -> None:
    for rel, body in repo.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", "base"]):
        subprocess.run([*GIT, *args], cwd=root, capture_output=True)


def play(scenario: Scenario) -> Outcome:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build(scenario.repo, root)

        ledger = Ledger(root=root)
        ledger.request = scenario.request
        ledger.claims = infer(scenario.request)
        touched = [a.edit[0] for a in scenario.acts if a.edit]
        ledger.touched = touched
        ledger.risk, ledger.domains = risk_of(touched or list(scenario.repo), scenario.request)

        clock = 0.0
        for act in scenario.acts:
            clock += 1.0
            if act.edit:
                target = root / act.edit[0]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(act.edit[1], encoding="utf-8")
                ledger.observe_edit(act.edit[0])
                continue
            records = parse(act.command, act.output, act.exit_code, root)
            for record in records:
                record.at = clock
            ledger.add(records)

        status = ledger.settle(scenario.last_message)
        blocked = status is not Status.VERIFIED
        missing = [c.obligation.key for v in ledger.verdicts() for c in v.missing]
        stale = [c.obligation.key for v in ledger.verdicts() for c in v.stale]
        failing = [f"{e.kind.value}:{e.identity}" for e in ledger._contradictions()]
        claims = ",".join(c.value for c in ledger.claims) or "-"
        detail = (
            f"claims={claims} risk={ledger.risk.value} evidence={len(ledger.evidence)}"
            + (f" missing={missing}" if missing else "")
            + (f" stale={stale}" if stale else "")
            + (f" failing={failing}" if failing else "")
        )
        return Outcome(scenario=scenario, blocked=blocked, status=status, detail=detail)


def main(argv: list[str]) -> int:
    verbose = "--verbose" in argv
    tag = None
    if "--tag" in argv:
        tag = argv[argv.index("--tag") + 1]

    pool = HELD_OUT if "--heldout" in argv else (SCENARIOS + HELD_OUT if "--all" in argv else SCENARIOS)
    scenarios = [s for s in pool if not tag or tag in s.tags]
    outcomes = [play(s) for s in scenarios]

    false_blocks = [o for o in outcomes if o.verdict == "FALSE BLOCK"]
    misses = [o for o in outcomes if o.verdict == "MISS"]
    complete = [o for o in outcomes if o.scenario.complete]
    incomplete = [o for o in outcomes if not o.scenario.complete]

    for outcome in outcomes:
        if verbose or outcome.verdict != "ok":
            mark = "  " if outcome.verdict == "ok" else "!!"
            print(f"{mark} {outcome.verdict:<12} {outcome.scenario.name:<32} "
                  f"{outcome.status.value:<13} {outcome.detail}")
            if outcome.verdict != "ok":
                print(f"                  truth: {outcome.scenario.why}")

    fb_rate = len(false_blocks) / len(complete) if complete else 0.0
    miss_rate = len(misses) / len(incomplete) if incomplete else 0.0
    print()
    print(f"scenarios          {len(outcomes)}  ({len(complete)} complete, {len(incomplete)} incomplete)")
    print(f"false-block rate   {fb_rate:.0%}  ({len(false_blocks)}/{len(complete)})   target <5%")
    print(f"miss rate          {miss_rate:.0%}  ({len(misses)}/{len(incomplete)})")
    if false_blocks:
        print(f"false blocks       {', '.join(o.scenario.name for o in false_blocks)}")
    if misses:
        print(f"misses             {', '.join(o.scenario.name for o in misses)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
