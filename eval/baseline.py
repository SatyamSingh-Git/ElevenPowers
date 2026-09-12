"""A pinned score, with an interval, that a rerun can be checked against.

    python -m eval.baseline --pinned --model claude-haiku-4-5-20251001
    python -m eval.baseline --show baseline.json
    python -m eval.baseline --compare first.json second.json

Every number this project published before Phase A came from a run nobody could
repeat: the corpus was whatever had been mined that week, the model was an alias
that could point somewhere else tomorrow, and the score was a bare percentage
with no statement of how much of it was luck. This module exists so the next
number is none of those things.

**Pinned means refused if not.** `--pinned` rejects a model alias, an unpinned
corpus and a dirty working tree, because each of them silently changes what is
being measured between two runs that carry the same name.

**The interval is over tasks, not over runs.** Fifteen tasks with three
replicates each is forty-five numbers and nowhere near forty-five independent
ones: a task an agent always solves contributes three identical successes. A
binomial interval over runs would be roughly sqrt(3) too narrow and would make a
rerun look like a contradiction. So the interval is a percentile bootstrap that
resamples **tasks**, carrying each task's replicates with it, which is the same
correction E2 forced on the paired comparison.

**Reproduces means overlapping, not equal.** Agent runs are stochastic; a rerun
producing the identical score would be suspicious rather than reassuring. What a
rerun must do is land inside the first run's interval, on the same pinned
corpus. `--compare` checks that, and refuses outright when the corpora differ —
two scores from two benchmarks are not a reproduction however close they look.
"""

from __future__ import annotations

import hashlib
import json
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

from .live import ARMS, Run, arm_order, environment, once
from .mined import load as load_mined
from .task import Task

BOOTSTRAP_DRAWS = 10_000


def corpus_fingerprint(lock: Path) -> str:
    """What was graded, in sixteen characters.

    Two scores are comparable only if this matches. A corpus is easy to change
    without noticing — one more instance mined, one repository updated — and a
    comparison across two of them is not a reproduction.
    """
    if not lock.exists():
        return ""
    pins = json.loads(lock.read_text(encoding="utf-8"))
    seed = json.dumps(sorted((p["origin"], p["base"], p["fix"]) for p in pins))
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


def is_alias(model: str) -> bool:
    """A pinned model names a version. `haiku` does not; `claude-haiku-4-5-…` does.

    The host resolves an alias at request time, so two sweeps a month apart can
    run different models and report one number. A digit-bearing suffix is a
    crude test and it separates the aliases that exist from the ids that do.
    """
    return "-" not in model or not any(ch.isdigit() for ch in model)


def working_tree_clean(root: Path) -> bool:
    done = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                          capture_output=True, text=True)
    return done.returncode == 0 and not done.stdout.strip()


def refusals(model: str, lock: Path, root: Path) -> list[str]:
    """Why this run would not be a pinned one, or an empty list.

    Separated from the command so both directions can be tested. A harness that
    refuses everything is not pinned, it is broken, and only the forward case
    tells those apart.
    """
    out = []
    if not model:
        out.append("--model is required: a baseline without a pinned model cannot be "
                   "compared with anything")
    elif is_alias(model):
        out.append(f"{model} is an alias. The host resolves it at request time, so two "
                   "sweeps can run different models and report one number. Pass the id "
                   "the host reports.")
    if not corpus_fingerprint(lock):
        out.append(f"no corpus lock at {lock}: build one with python -m eval.corpus --lock")
    if not working_tree_clean(root):
        out.append("the working tree is dirty; the harness that produced the score would "
                   "not be recoverable from the commit")
    return out


def interval(per_task: list[float], seed: int, mass: float = 0.95) -> tuple[float, float]:
    """A percentile bootstrap over tasks, seeded so the interval is reproducible.

    Resampling tasks rather than runs is the whole point. Replicates of one task
    are correlated — often perfectly, when an agent solves or fails a task every
    time — and treating them as independent observations narrows the interval by
    about the square root of the replicate count. That is how a rerun that
    agrees comes to look like a contradiction.
    """
    if not per_task:
        return 0.0, 1.0
    if len(per_task) == 1:
        return 0.0, 1.0          # one task cannot bound anything
    draw = random.Random(seed)
    n = len(per_task)
    means = sorted(statistics.fmean(draw.choices(per_task, k=n))
                   for _ in range(BOOTSTRAP_DRAWS))
    low = means[int((1 - mass) / 2 * BOOTSTRAP_DRAWS)]
    high = means[min(BOOTSTRAP_DRAWS - 1, int((1 + mass) / 2 * BOOTSTRAP_DRAWS))]
    return low, high


def by_task(runs: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for run in runs:
        out.setdefault(run["task"], []).append(run)
    return out


def reached_the_model(runs: list[dict]) -> dict:
    """What was actually sent, rather than what was installed.

    An arm can declare a plugin, load nothing, and score identically to plain —
    which is audit finding E4, and the reason it went unnoticed for so long is
    that nothing measured the difference. Tokens on the way in are the closest
    honest proxy available from a non-interactive run: a configuration that adds
    instructions adds context, and one that adds none did not arrive.
    """
    sent = [r["context_tokens"] for r in runs if r.get("context_tokens")]
    if not sent:
        return {}
    return {"runs": len(sent), "median": int(statistics.median(sent)),
            "low": min(sent), "high": max(sent)}


def score(rows: list[dict], seed: int) -> dict:
    tasks = by_task(rows)
    per_task = [statistics.fmean([bool(r["resolved"]) for r in group])
                for group in tasks.values()]
    setup = [r for r in rows if r.get("outcome") == "setup"]
    low, high = interval(per_task, seed)
    return {
        "tasks": len(tasks),
        "runs": len(rows),
        "resolved": statistics.fmean(per_task) if per_task else 0.0,
        "low": low,
        "high": high,
        "setup_failures": len(setup),
        "context": reached_the_model(rows),
    }


def show(path: Path) -> int:
    report = json.loads(path.read_text(encoding="utf-8"))
    s = report["score"]
    print(f"model    {report['model']}")
    print(f"corpus   {report['corpus']}  ({s['tasks']} tasks, {s['runs']} runs)")
    print(f"seed     {report['seed']}")
    print()
    print(f"resolved {s['resolved']:.1%}   95% interval {s['low']:.1%} to {s['high']:.1%}")
    if s["setup_failures"]:
        print(f"         {s['setup_failures']} run(s) failed as setup and are not scored "
              f"against the agent")

    if s["context"]:
        c = s["context"]
        print()
        print(f"context reaching the model: median {c['median']:,} tokens "
              f"(from {c['low']:,} to {c['high']:,} over {c['runs']} run(s))")

    bands = report.get("bands") or {}
    if bands:
        print()
        print(f"{'band':<14}{'tasks':>6}{'resolved':>10}")
        for name, part in bands.items():
            print(f"{name:<14}{part['tasks']:>6}{part['resolved']:>10.0%}")
        print("Bands are labels, not filters — a gain in one of them is not a gain.")

    width = s["high"] - s["low"]
    print()
    if width > 0.4:
        print(f"The interval spans {width:.0%}. This is a pilot: it bounds almost nothing,")
        print("and reporting the point estimate alone would be a claim it cannot support.")
    return 0


def compare(first: Path, second: Path) -> int:
    a, b = (json.loads(p.read_text(encoding="utf-8")) for p in (first, second))
    if a["corpus"] != b["corpus"]:
        print(f"different corpora: {a['corpus']} vs {b['corpus']}")
        print("Two scores from two benchmarks are not a reproduction, however close.")
        return 1
    if a["model"] != b["model"]:
        print(f"different models: {a['model']} vs {b['model']}")
        return 1

    inside = a["score"]["low"] <= b["score"]["resolved"] <= a["score"]["high"]
    back = b["score"]["low"] <= a["score"]["resolved"] <= b["score"]["high"]
    print(f"first    {a['score']['resolved']:.1%}  [{a['score']['low']:.1%}, {a['score']['high']:.1%}]")
    print(f"second   {b['score']['resolved']:.1%}  [{b['score']['low']:.1%}, {b['score']['high']:.1%}]")
    print()
    if inside and back:
        print("Each score falls inside the other's interval: the rerun reproduces.")
        return 0
    print("The scores do not cover each other. Either the effect is real or the")
    print("interval is too narrow for the number of tasks; both need more tasks,")
    print("not a rerun.")
    return 1


def run_baseline(tasks: list[Task], arm: str, model: str, replicates: int,
                 bundles: Path, seed: int) -> list[Run]:
    shuffler = random.Random(seed)
    out: list[Run] = []
    for task in tasks:
        for which in arm_order([arm], shuffler):
            for _ in range(replicates):
                run = once(task, which, model, bundles)
                out.append(run)
                print(f"  {task.name:<26}{which:<9}"
                      f"{'resolved' if run.resolved else run.outcome:<10}"
                      f"{run.turns:>3} turns {run.seconds:>5.0f}s ${run.cost:.2f}",
                      flush=True)
    return out


def main(argv: list[str]) -> int:
    def option(flag, default):
        return argv[argv.index(flag) + 1] if flag in argv else default

    if "--show" in argv:
        return show(Path(option("--show", "baseline.json")))
    if "--compare" in argv:
        rest = [a for a in argv[argv.index("--compare") + 1:] if not a.startswith("-")]
        if len(rest) < 2:
            print(__doc__)
            return 1
        return compare(Path(rest[0]), Path(rest[1]))

    model = option("--model", "")
    arm = option("--arm", "vanilla")
    replicates = int(option("--runs", "3"))
    seed = int(option("--seed", "0")) or int(time.time())
    lock = Path(option("--lock", "eval/corpus.lock"))
    root = Path(__file__).resolve().parents[1]

    if "--pinned" in argv:
        why = refusals(model, lock, root)
        if why:
            print("refusing to run unpinned:")
            for line in why:
                print(f"  - {line}")
            return 1

    tasks = load_mined()
    if not tasks:
        print("no mined tasks. Set EP_MINED to a corpus built by python -m eval.corpus")
        return 1
    if arm not in ARMS:
        print(f"unknown arm {arm}; one of {', '.join(ARMS)}")
        return 1

    bundles = Path(option("--bundles", "runs"))
    print(f"model    {model}")
    print(f"corpus   {corpus_fingerprint(lock)}  ({len(tasks)} tasks)")
    print(f"seed     {seed}   arm {arm}, {replicates} replicate(s) per task")
    print(f"bundles  {bundles}")
    print()

    runs = run_baseline(tasks, arm, model, replicates, bundles, seed)
    rows = [r.__dict__ for r in runs]
    report = {
        "model": model,
        "arm": arm,
        "corpus": corpus_fingerprint(lock),
        "seed": seed,
        "environment": environment(),
        "score": score(rows, seed),
        "bands": bands_of(rows, {t.name: (t.source or {}).get("gold_lines", 0)
                                 for t in tasks}),
        "runs": rows,
    }
    out = Path(option("--out", "baseline.json"))
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"\nwrote {out}")
    return show(out)


def bands_of(rows: list[dict], gold_lines: dict[str, int]) -> dict:
    """Resolve rate per difficulty band, so a gain cannot hide in an average.

    A task whose size is not known is reported as `unknown`, never folded into a
    band. Defaulting a missing size to zero would file every task under "empty"
    the moment the run and the corpus disagreed about a name, and the table
    would look complete while describing nothing — which is the shape of most
    defects this project has had to find twice.
    """
    from .corpus import band

    rates: dict[str, list[float]] = {}
    for name, group in by_task(rows).items():
        key = band(gold_lines[name]) if name in gold_lines else "unknown"
        rates.setdefault(key, []).append(
            statistics.fmean([bool(r["resolved"]) for r in group]))
    return {key: {"tasks": len(v), "resolved": statistics.fmean(v)}
            for key, v in sorted(rates.items())}


if __name__ == "__main__":
    sys.exit(main(sys.argv))
