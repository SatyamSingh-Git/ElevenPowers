"""Read a live run and say what it does and does not show.

Usage: python -m eval.analyse runs.json

Three arms on sixteen tasks is a small experiment, and a small experiment
reported as a pair of percentages will mislead whoever reads it, including the
person who ran it. The first live result on the simple suite moved the gap from
12 percent to zero, which sounds decisive and rested on a single task changing
hands.

So the arithmetic that says how much to believe is part of the harness rather
than something applied afterwards when the numbers look good.
"""

from __future__ import annotations

import json
import sys
from math import comb
from pathlib import Path

BASELINE = "vanilla"


def load(path: Path) -> dict[str, dict[str, dict]]:
    runs = json.loads(path.read_text(encoding="utf-8"))
    table: dict[str, dict[str, dict]] = {}
    for run in runs:
        table.setdefault(run["task"], {})[run["arm"]] = run
    return table


def mcnemar(better: int, worse: int) -> float:
    """Two-sided exact test on the pairs that disagree.

    Only the discordant pairs carry information: tasks both arms resolve, or
    both fail, say nothing about which arm is better. With b of them favouring
    one arm and c the other, the null hypothesis is a fair coin over b + c
    flips.
    """
    n = better + worse
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(min(better, worse) + 1))
    return min(1.0, 2 * tail / 2 ** n)


def rates(rows: list[dict]) -> dict:
    n = len(rows)
    claimed = sum(r["claimed"] for r in rows) / n
    resolved = sum(r["resolved"] for r in rows) / n
    return {
        "n": n,
        "claimed": claimed,
        "resolved": resolved,
        "gap": claimed - resolved,
        "turns": sum(r["turns"] for r in rows) / n,
        "seconds": sum(r["seconds"] for r in rows) / n,
        "cost": sum(r["cost"] for r in rows),
        "blocks": sum(r["blocks"] for r in rows),
    }


def report(table: dict[str, dict[str, dict]]) -> None:
    arms = sorted({arm for row in table.values() for arm in row},
                  key=lambda a: (a != BASELINE, a))
    print(f"{'arm':<9}{'n':>4}{'claimed':>9}{'resolved':>10}{'gap':>7}"
          f"{'turns':>7}{'blocks':>8}{'cost':>8}")
    summary = {}
    for arm in arms:
        rows = [row[arm] for row in table.values() if arm in row]
        summary[arm] = rates(rows)
        s = summary[arm]
        print(f"{arm:<9}{s['n']:>4}{s['claimed']:>8.0%}{s['resolved']:>10.0%}"
              f"{s['gap']:>7.0%}{s['turns']:>7.1f}{s['blocks']:>8}{s['cost']:>8.2f}")

    base = summary.get(BASELINE)
    if not base:
        return

    # An arm can only overturn a task the baseline failed, so the number of
    # baseline failures is a ceiling on the evidence this run can produce. Worth
    # printing before the p-values, because a run that cannot reach significance
    # however well it goes should be described as a pilot rather than a result.
    failures = sum(1 for row in table.values() if not row[BASELINE]["resolved"])
    best = mcnemar(failures, 0)
    print()
    print(f"the baseline failed {failures} of {base['n']} tasks, so the strongest "
          f"result available here is p = {best:.3f}"
          + ("" if best <= 0.05 else "; this run is a pilot, not a verdict"))

    print()
    print(f"against {BASELINE}, on the tasks where the two disagree")
    for arm in arms:
        if arm == BASELINE:
            continue
        better = [t for t, row in table.items()
                  if BASELINE in row and arm in row
                  and row[arm]["resolved"] and not row[BASELINE]["resolved"]]
        worse = [t for t, row in table.items()
                 if BASELINE in row and arm in row
                 and row[BASELINE]["resolved"] and not row[arm]["resolved"]]
        p = mcnemar(len(better), len(worse))
        verdict = ("nothing to see" if p > 0.1 else
                   "suggestive" if p > 0.05 else "significant at 0.05")
        print(f"  {arm:<8} fixed {len(better)}, broke {len(worse)}   "
              f"p = {p:.3f}   {verdict}")
        if better:
            print(f"           gained: {', '.join(sorted(better))}")
        if worse:
            print(f"           lost:   {', '.join(sorted(worse))}")
        cost = summary[arm]["cost"] / base["cost"] if base["cost"] else 0
        turns = summary[arm]["turns"] / base["turns"] if base["turns"] else 0
        print(f"           cost x{cost:.1f}, turns x{turns:.1f}")

    gate = summary.get("gate")
    if gate and gate["blocks"]:
        already = sum(
            1 for row in table.values()
            if row.get("gate", {}).get("blocks") and row.get(BASELINE, {}).get("resolved")
        )
        blocked = sum(1 for row in table.values() if row.get("gate", {}).get("blocks"))
        print()
        print(f"the gate stopped {blocked} of {gate['n']} runs at their first attempt to finish")
        print(f"on {already} of those, a plain agent had already resolved the same task,")
        print("so the block bought evidence for work that was most likely already correct")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    report(load(Path(argv[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
