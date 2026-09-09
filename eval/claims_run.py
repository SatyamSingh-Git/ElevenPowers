"""Measure claim inference against what real turns actually did.

Usage: python -m eval.claims_run [--verbose] [--limit N] [--cases]

Inferring a claim is what switches the runtime on. Infer one where there was no
work and the gate demands proof of something that never happened, which is a
false block on a turn that was only a conversation. Infer none where there was
work and the whole layer sits out the task it exists for.

Both rates are reported, because they trade against each other and a single
accuracy figure would hide which way the errors run.
"""

from __future__ import annotations

import sys
from collections import Counter

from core.claims import infer, opens_new_task
from core.scope import is_manifest, is_prose

from .claim_cases import CASES
from .prompts import Sample, collect


def claim_opens(item: Sample) -> bool:
    """What the runtime ends up with, mirroring `Ledger.observe_edit`.

    A claim comes from the prompt when the prompt states one, and otherwise from
    the first source edit. A prompt that explicitly asked for something else is
    left alone, so answering a question is not turned into a claim by an
    incidental edit.
    """
    if infer(item.prompt):
        return True
    if opens_new_task(item.prompt):
        return False
    return any(not is_manifest(p) and not is_prose(p) for p in item.edited)


def measure(samples: list[Sample], verbose: bool = False) -> dict:
    box = Counter()
    over: list[Sample] = []
    missed: list[Sample] = []

    for item in samples:
        claimed = claim_opens(item)
        box[(claimed, item.changed_code)] += 1
        if claimed and not item.changed_code:
            over.append(item)
        elif not claimed and item.changed_code:
            missed.append(item)

    quiet = box[(False, False)] + box[(True, False)]
    working = box[(False, True)] + box[(True, True)]
    result = {
        "turns": len(samples),
        "quiet": quiet,
        "working": working,
        "over": len(over),
        "missed": len(missed),
        "over_rate": len(over) / quiet if quiet else 0.0,
        "miss_rate": len(missed) / working if working else 0.0,
        # Some turns change the repository in ways that name no file the runtime
        # can see: `mkdir`, `npm install`, `git checkout`. Counted separately, so
        # the inference is not blamed for a gap in what it is shown.
        "invisible": sum(1 for m in missed if not m.edited),
        "visible": sum(1 for s in samples if s.changed_code and s.edited),
        "visible_missed": sum(1 for m in missed if m.edited),
    }
    if verbose:
        for item in over[:15]:
            print(f"  over   {[c.value for c in infer(item.prompt)]} :: {item.prompt[:90]}")
        for item in missed[:15]:
            print(f"  missed edits={item.edits} writes={item.writes} :: {item.prompt[:90]}")
    return result


def run_cases() -> tuple[int, int]:
    """The hand-labelled prompts, which the behavioural proxy cannot settle."""
    wrong = []
    for case in CASES:
        claims = [c.value for c in infer(case.prompt)]
        if bool(claims) is not case.should_claim:
            wrong.append((case, claims))
        elif case.claim and case.claim not in claims:
            wrong.append((case, claims))
    for case, claims in wrong:
        want = case.claim or ("a claim" if case.should_claim else "no claim")
        print(f"  !! got {claims or 'none'}, want {want} :: {case.prompt[:80]}")
        print(f"     {case.why}")
    return len(CASES) - len(wrong), len(CASES)


def main(argv: list[str]) -> int:
    limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else 0

    if "--cases" not in argv:
        samples = collect(limit=limit)
        result = measure(samples, verbose="--verbose" in argv)
        print(f"turns              {result['turns']}  "
              f"({result['working']} changed code, {result['quiet']} did not)")
        print(f"over-claim rate    {result['over_rate']:.0%}  "
              f"({result['over']}/{result['quiet']})   a claim where no work happened")
        print(f"miss rate          {result['miss_rate']:.0%}  "
              f"({result['missed']}/{result['working']})   no claim where work happened")
        visible = result["visible"]
        print(f"                   {result['invisible']} of those named no file the runtime "
              f"can see (mkdir, npm install, git checkout)")
        print(f"                   {result['visible_missed']}/{visible} "
              f"({result['visible_missed'] / visible:.0%}) on turns whose change was visible")
        print("                   ground truth is the turn's own behaviour, which is a proxy")
        print()

    passed, total = run_cases()
    print(f"labelled prompts   {passed}/{total} correct")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
