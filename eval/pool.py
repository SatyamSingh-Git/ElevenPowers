"""Is a selector worth building, or would one do more harm than good?

    python -m eval.pool --from-bundles results/chunks results/bundles-A

PLAN §5.1: for a pool of N candidates, *pool coverage* is the fraction of tasks
where at least one candidate is correct, *selected success* is the fraction
where the chosen one is correct, and the difference is **selection regret**.
§5.1 says measure that before building a selector. Phase B2.2 says measure it
before building anything at all, because it is free: every attempt in `results/`
was already paid for and already graded.

**The reference point this exists to locate us against.** A fixed-pool
diagnostic that swapped the selector and measured gain *and harm* found
execution-based selection worth +8.14pp at 0% harm, a same-model LLM judge
+3.50pp at 4.69% harm — and on a benchmark offering only 3.03 points of oracle
gap, **every selector it tried underperformed the baseline**, destroying more
correct answers than it rescued.

**Read from the HTML on 2026-09-22, and the three numbers are exactly right —
which makes where they come from the interesting part.** All three are verbatim
(arXiv 2607.17531): `+8.14pp` at `0/2089 = 0%` harm for public-test execution,
`+3.50pp` while harming `98/2089 = 4.69%` of first-sample-correct cases for the
same-family LLM judge, and *"the oracle gap is only 18/594 = 3.03pp"* where
every selector went net-negative.

**But the first two are LiveCodeBench, and the third is GPQA-Diamond.** The
benchmark that produced the "do not build a selector" line is multiple-choice
science; the paper's own *coding* benchmark is where execution-based selection
scored its best result, at **zero** harm. So the threshold was imported here
from the one benchmark in that paper least like this work, and the one most like
it points the other way.

That does not make selection a good idea on this corpus - a selector's expected
value is the mass it rescues minus the mass it damages, and that is still
unmeasured here. It does mean the number below is a **reference point**, not a
law: it says what to check, not what to conclude.

So this module reports which side of that line a pool sits on, and the decision
needs the other half: estimated rescue, estimated harm to the incumbent, and the
same compute spent on ordinary extra attempts for comparison.

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

# The oracle gap below which one published study's selectors went net-negative.
# Not a rule of thumb, and not a law either: that study's low-gap case is
# GPQA-Diamond, a multiple-choice science benchmark, while its coding benchmark
# showed execution-based selection at +8.14pp and 0% harm. Cited in full above.
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
        out.append((root.name, task, arm, outcome, int(stamp.group(1)) if stamp else 0,
                    condition(man)))
    return out


def condition(manifest: dict) -> str:
    """The experimental condition an attempt actually ran under.

    A directory name is a label somebody typed. The manifest records what the
    run *was* - which model was asked for, what environment it was handed, what
    limits it was given - and two attempts are interchangeable candidates only
    if those agree. `results/closedbook` is the standing example: it is a
    different condition by construction, and nothing but its folder name said
    so.

    Fields absent from an older manifest degrade to "unknown" rather than to a
    false match, which is the safe direction: an attempt whose conditions cannot
    be established does not silently join a pool.

    **The dimension that mattered was missing, and finding that out is the
    point.** This was first written using model, limits and task environment,
    and `results/closedbook` - the standing example of a different condition -
    came back byte-identical to the open-book sweeps on all three. What made it
    different was what it could *reach*, and no manifest recorded that. So
    `access` joins the key, bundles written before it exists read as
    `access=unrecorded`, and **unrecorded is a distinct value from `open`** -
    because "nobody wrote it down" is not a measurement.
    """
    limits = manifest.get("limits") or {}
    env = manifest.get("env") or {}
    access = manifest.get("access") or {}
    return "|".join([
        str(manifest.get("model_asked") or manifest.get("model") or "unknown-model"),
        f"agent={limits.get('agent_seconds', '?')}",
        f"suite={limits.get('suite_seconds', '?')}",
        ("env=" + ",".join(f"{k}={v}" for k, v in sorted(env.items()))) if env else "env=-",
        "access=" + (str(access.get("registry", "?")) if access.get("recorded")
                     else "unrecorded"),
    ])


def pools(rows) -> dict[tuple[str, str, str], list[str]]:
    """Attempts grouped into the pool a selector would have chosen from.

    Rows may carry a sixth element, the effective condition. It is optional so
    a hand-built row still works, and when it is there it is kept beside the
    outcome so `measure` can refuse to pool across conditions.
    """
    grouped: dict[tuple[str, str, str], list[tuple[int, str, str]]] = defaultdict(list)
    for row in rows:
        sweep, task, arm, outcome, when = row[:5]
        here = row[5] if len(row) > 5 else ""
        grouped[(sweep, task, arm)].append((when, outcome, here))
    return {k: [(o, c) for _, o, c in sorted(v)] for k, v in grouped.items()}


def measure(grouped, sweep: str | None, arm: str) -> dict | None:
    """Coverage, a random pick, the last attempt, and the gap between them."""
    # Concatenated, not overwritten. Keyed by task alone, a second sweep's
    # attempt at the same task replaced the first instead of joining it - so
    # ALL POOLED reported one attempt and zero coverage where the union has two
    # attempts, full coverage and a 50% random pick. The same dict-comprehension
    # shape that laundered a failing monorepo package into a passing record.
    picked: dict[str, list[str]] = defaultdict(list)
    conditions: set[str] = set()
    sweeps_seen: set[str] = set()
    for (s, t, a), outs in grouped.items():
        if a == arm and (sweep is None or s == sweep):
            sweeps_seen.add(s)
            for entry in outs:
                outcome, here = entry if isinstance(entry, tuple) else (entry, "")
                picked[t].append(outcome)
                if here:
                    conditions.add(here)
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
        # How many distinct experimental conditions these attempts actually ran
        # under, read from each manifest rather than from a folder name. More
        # than one means these are not interchangeable candidates and the pool
        # is a mixture, whatever the row is labelled.
        "conditions": len(conditions),
        # True when the bundles cannot say what the run could reach.
        # Distinct from the count above: every sweep here may agree on
        # model and limits and still be incomparable, which is exactly
        # what `results/closedbook` is.
        "access_unrecorded": any("access=unrecorded" in c for c in conditions),
        "sweeps": len(sweeps_seen),
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
    if m.get("conditions", 0) > 1:
        verdict_conditions(m)
    if m["gap"] < HARM_LINE:
        print(f"  Under the {HARM_LINE:.0f}-point reference line, where one published fixed-pool "
              f"study found every selector it tried destroying more correct answers than it "
              f"rescued. That is a reason to look upstream first - generation and reproduction "
              f"synthesis, PLAN §5.13 - and not, on its own, a reason to cancel selection: what "
              f"decides it is rescued mass minus damaged mass, measured here (PLAN §10).")
    else:
        print(f"  Above the {HARM_LINE:.0f}-point line: {m['gap']:.1f} points a selector could in "
              f"principle recover. Measure correct-candidate survival through every filter before "
              f"believing it (PLAN §6).")


def verdict_conditions(m: dict) -> None:
    """Say when a row is a mixture rather than a pool.

    Read from each manifest - the model asked for, the time limits, the
    environment handed over - and not from a directory name. A directory name
    is a label somebody typed; the standing example is `results/closedbook`,
    which is a different condition by construction and was flagged only by a
    hand-written paragraph naming that one folder. A sweep added next year
    under a different model would have been pooled in silently.
    """
    print(f"  MIXED CONDITIONS: {m['sweep']} / {m['arm']} pools attempts from "
          f"{m['conditions']} different effective configurations. They are not "
          f"interchangeable candidates, so coverage and the gap on this row describe a "
          f"mixture and not a pool. Compare per condition instead.")


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
    # The warning belongs here most of all: this is the row somebody quotes.
    # Previously the only thing saying these runs were incomparable was the
    # paragraph above, which names one directory by hand - so a sweep added
    # next year under a different model would be pooled in silently. Now it is
    # read from the manifests.
    for m in pooled:
        if m.get("conditions", 0) > 1:
            verdict_conditions(m)
        elif m.get("access_unrecorded") and m.get("sweeps", 1) > 1:
            print(f"  UNVERIFIABLE POOL: {m['sweep']} / {m['arm']} joins {m['sweeps']} sweeps "
                  f"whose bundles do not record what each run could reach. They agree on "
                  f"model, limits and task environment, and that is not enough - "
                  f"`results/closedbook` agrees on all three and is a different experiment. "
                  f"Runs written from now on record it; these cannot be checked.")

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
