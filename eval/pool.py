"""Is a selector worth building, or would one do more harm than good?

    python -m eval.pool --from-bundles results/chunks results/bundles-A

PLAN §5.1: for a pool of N candidates, *pool coverage* is the fraction of tasks
where at least one candidate is correct, *selected success* is the fraction
where the chosen one is correct, and the difference is **selection regret**.
§5.1 says measure that before building a selector. Phase B2.2 says measure it
before building anything at all, because it is free: every attempt in `results/`
was already paid for and already graded.

**The threshold this exists to test.** A fixed-pool diagnostic that swapped the
selector and measured gain *and harm* found execution-based selection worth
+8.14pp at 0% harm, a same-model LLM judge +3.50pp at 4.69% harm — and on a
benchmark offering only 3.03 points of oracle gap, **every selector it tried
underperformed the baseline**, destroying more correct answers than it rescued.
So a gap under about four points is not a small opportunity; it is a reason not
to build. This module exists to find out which side of that line we are on.

**What "selected success" means when there is no selector.** Nothing here chose
anything: the attempts are independent runs of the same task. So the honest
baseline is the expected value of picking one uniformly at random. `last` is
reported beside it because a session that simply keeps going submits its latest
attempt, and §5.6 warns that a long attempt ends at its latest patch rather than
its best.

**Why a pool is keyed by sweep, task and arm.** Pooling a task's attempts across
sweeps would treat runs made under different conditions as interchangeable
candidates, and one of these directories — `closedbook` — is a *different
condition by construction*. Mixing it with open-book runs would inflate coverage
with attempts the others never had access to. Arms are separated for the same
reason: they are different treatments, and pooling them measures the treatment
rather than the selection. The pooled total is printed last, and labelled as the
thing not to quote.

**Three things that bound every number below.**

- *Replication bounds the gap.* A task attempted once cannot show any gap at
  all, so tasks are counted by how many attempts they have and single-attempt
  tasks are reported separately rather than quietly averaged in.
- *`setup` is not a failure of the agent.* An environment that broke under a run
  says nothing about the candidate, so those attempts are excluded from the
  rates and counted in plain sight.
- *Most of this corpus was not closed-book.* Twenty-four of a hundred runs named
  their own task's fix commit. Coverage measured under answer access is an upper
  bound, and `eval.exposure` reports the floor. A gap is more robust to this than
  an absolute score — candidates start from the same retrieved state — but it is
  not immune, and nothing here filters the flagged runs, for the reason
  `eval.exposure` gives.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# An attempt that never got to run the agent's code is evidence about the
# machine, not about the candidate.
NOT_THE_AGENT = {"setup"}

# Under about this many points of oracle gap, measured selectors do more harm
# than good. Not a rule of thumb — a reported threshold, cited in the docstring.
HARM_LINE = 4.0

# Bundle directories end in the run's start time, which is the only ordering
# that makes "the last attempt" mean anything. Sorting by name would order
# `--1789249833456` against `--178925...` lexically, which happens to agree here
# and would stop agreeing the moment the clock gained a digit.
STAMP = re.compile(r"--(\d+)$")


def attempts(root: Path) -> list[tuple[str, str, str, str, int]]:
    """Every graded attempt under `root`, as (sweep, task, arm, outcome, when)."""
    out = []
    for manifest in sorted(root.rglob("manifest.json")):
        bundle = manifest.parent
        grade = bundle / "grade.json"
        if not grade.exists():
            continue
        try:
            man = json.loads(manifest.read_text(encoding="utf-8"))
            got = json.loads(grade.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        task, arm, outcome = man.get("task"), man.get("arm"), got.get("outcome")
        if not (task and arm and outcome):
            continue
        stamp = STAMP.search(bundle.name)
        out.append((root.name, task, arm, outcome, int(stamp.group(1)) if stamp else 0))
    return out


def pools(rows) -> dict[tuple[str, str, str], list[str]]:
    """Attempts grouped into the pool a selector would have chosen from."""
    grouped: dict[tuple[str, str, str], list[tuple[int, str]]] = defaultdict(list)
    for sweep, task, arm, outcome, when in rows:
        grouped[(sweep, task, arm)].append((when, outcome))
    return {k: [o for _, o in sorted(v)] for k, v in grouped.items()}


def measure(grouped, sweep: str | None, arm: str) -> dict | None:
    """Coverage, a random pick, the last attempt, and the gap between them."""
    picked = {t: outs for (s, t, a), outs in grouped.items()
              if a == arm and (sweep is None or s == sweep)}
    before = sum(len(v) for v in picked.values())
    pool = {t: [o for o in outs if o not in NOT_THE_AGENT] for t, outs in picked.items()}
    pool = {t: outs for t, outs in pool.items() if outs}
    if not pool:
        return None

    replicated = sum(1 for outs in pool.values() if len(outs) > 1)
    covered = sum(any(o == "resolved" for o in outs) for outs in pool.values())
    # The gap is produced by these and nothing else. A task all of whose
    # attempts resolve contributes 1 - 1 = 0; one where none resolve
    # contributes 0 - 0 = 0. Only a task whose attempts disagree can leave
    # anything on the table, so `mixed` is the mechanism behind the number and
    # the right thing to check a surprising gap against.
    mixed = sum(1 for outs in pool.values()
                if 0 < sum(o == "resolved" for o in outs) < len(outs))
    # A random pick from a task's own pool, averaged over tasks, rather than a
    # mean over all attempts: a task with six attempts must not outvote one with
    # two when the question is per-task success.
    random_pick = sum(sum(o == "resolved" for o in outs) / len(outs)
                      for outs in pool.values()) / len(pool)
    last = sum(outs[-1] == "resolved" for outs in pool.values()) / len(pool)

    return {
        "sweep": sweep or "ALL POOLED",
        "arm": arm,
        "tasks": len(pool),
        "replicated": replicated,
        "mixed": mixed,
        "attempts": sum(len(v) for v in pool.values()),
        "dropped_setup": before - sum(len(v) for v in pool.values()),
        "coverage": covered / len(pool),
        "random_pick": random_pick,
        "last": last,
        "gap": (covered / len(pool) - random_pick) * 100,
    }


def table(results: list[dict]) -> None:
    head = (f"{'sweep':22s} {'arm':8s} {'tasks':>6s} {'2+':>4s} {'mixed':>6s} {'runs':>5s} "
            f"{'coverage':>9s} {'random':>8s} {'last':>7s} {'gap':>8s}")
    print(head)
    print("-" * len(head))
    for m in results:
        print(f"{m['sweep']:22s} {m['arm']:8s} {m['tasks']:6d} {m['replicated']:4d} "
              f"{m['mixed']:6d} {m['attempts']:5d} {m['coverage']:8.1%} {m['random_pick']:8.1%} "
              f"{m['last']:7.1%} {m['gap']:+7.1f}p")


def verdict(m: dict) -> None:
    print(f"\n{m['sweep']} / {m['arm']}: coverage {m['coverage']:.1%}, a random pick "
          f"{m['random_pick']:.1%} — selection regret {m['gap']:+.1f} points.")
    if m["replicated"] < m["tasks"]:
        print(f"  {m['tasks'] - m['replicated']} of {m['tasks']} tasks have a single attempt "
              f"and cannot show any gap, so this understates what a replicated pool would show.")
    if m["mixed"]:
        print(f"  The whole gap comes from {m['mixed']} task(s) whose attempts disagree — a task "
              f"that always passes, or always fails, contributes nothing to it. At this corpus "
              f"size that makes the figure a statement about per-run flakiness on a handful of "
              f"tasks, not about a stable property of the pool.")
    elif m["replicated"]:
        print("  No task's attempts disagree, so there is nothing for any selector to pick between.")
    if m["dropped_setup"]:
        print(f"  {m['dropped_setup']} attempt(s) excluded as `setup`: the machine, not the candidate.")
    if m["gap"] < HARM_LINE:
        print(f"  Under the {HARM_LINE:.0f}-point line. On this evidence a selector is not worth "
              f"building: below this gap, measured selectors destroy more correct answers than "
              f"they rescue. The investment belongs upstream, in generation and in reproduction "
              f"synthesis (PLAN §5.13).")
    else:
        print(f"  Above the {HARM_LINE:.0f}-point line: {m['gap']:.1f} points a selector could in "
              f"principle recover. Measure correct-candidate survival through every filter before "
              f"believing it (PLAN §6).")


def report(roots: list[Path]) -> int:
    rows = []
    for root in roots:
        if not root.exists():
            print(f"missing: {root}")
            return 1
        found = attempts(root)
        print(f"{root}: {len(found)} graded attempts")
        rows += found
    if not rows:
        print("no graded bundles found")
        return 1

    grouped = pools(rows)
    sweeps = sorted({s for s, _, _ in grouped})
    arms = sorted({a for _, _, a in grouped})

    per_sweep = [m for s in sweeps for a in arms if (m := measure(grouped, s, a))]
    print()
    table(per_sweep)
    for m in per_sweep:
        verdict(m)

    print("\n" + "=" * 72)
    print("Pooled across sweeps — NOT a figure to quote. `closedbook` is a different")
    print("condition by construction, so pooling lends its tasks attempts the others")
    print("never had. Shown only so the per-sweep rows above can be checked against it.")
    print("=" * 72)
    pooled = [m for a in arms if (m := measure(grouped, None, a))]
    table(pooled)

    print("\nCoverage is measured with answer access on most of this corpus (PLAN §4.1);")
    print("it is an upper bound. `python -m eval.exposure` reports the floor.")
    return 0


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rest = [a for a in argv[1:] if not a.startswith("-")]
    if "--from-bundles" not in argv or not rest:
        print(__doc__)
        return 1
    return report([Path(r) for r in rest])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
