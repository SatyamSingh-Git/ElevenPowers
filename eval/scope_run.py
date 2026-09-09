"""Measure the scope guard against its labelled cases.

Usage: python -m eval.scope_run [--verbose]

Same framing as the completion gate: a guard that interrupts correct work is
worse than no guard, so false asks are the number that matters.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from core.scope import unrelated

from .scope_cases import CASES, ScopeCase


def play(case: ScopeCase) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for rel in case.repo:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x\n", encoding="utf-8")
        reason = unrelated(case.target, case.seen, case.request, case.exists)
        return bool(reason), reason


def main(argv: list[str]) -> int:
    verbose = "--verbose" in argv
    false_asks: list[ScopeCase] = []
    misses: list[ScopeCase] = []

    for case in CASES:
        asked, reason = play(case)
        wrong = asked != case.should_ask
        if wrong:
            (false_asks if asked else misses).append(case)
        if verbose or wrong:
            mark = "!!" if wrong else "  "
            verdict = "FALSE ASK" if (wrong and asked) else ("MISS" if wrong else "ok")
            print(f"{mark} {verdict:<10} {case.name:<34} asked={str(asked):<5} {reason}")
            if wrong:
                print(f"              truth: {case.why}")

    quiet = [c for c in CASES if not c.should_ask]
    noisy = [c for c in CASES if c.should_ask]
    print()
    print(f"cases            {len(CASES)}  ({len(quiet)} should stay silent, {len(noisy)} should speak)")
    print(f"false-ask rate   {len(false_asks) / len(quiet):.0%}  ({len(false_asks)}/{len(quiet)})   target 0%")
    print(f"miss rate        {len(misses) / len(noisy):.0%}  ({len(misses)}/{len(noisy)})")
    if false_asks:
        print(f"false asks       {', '.join(c.name for c in false_asks)}")
    if misses:
        print(f"misses           {', '.join(c.name for c in misses)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
