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


def graded_fingerprint(tasks: list[Task]) -> str:
    """What is actually graded, which is not the same as which commits are pinned.

    The lock names origin, base and fix. The preservation sets decide verdicts,
    and they are resolved on whichever machine built the corpus: one click node
    carried `importlib.metadata.version("click")` inside its id, so two builds
    of the same pins disagreed about what counts as a regression while reporting
    the same fingerprint. A comparison across those two is not a reproduction
    either, and nothing said so.
    """
    seed = json.dumps(sorted(
        (t.name, list(t.source["f2p"]), list(t.source.get("p2p") or []))
        for t in tasks))
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


def corpus_fingerprint(lock: Path) -> str:
    """Which commits were pinned, in sixteen characters.

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
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
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
    graded = (a.get("graded"), b.get("graded"))
    if all(graded) and graded[0] != graded[1]:
        print(f"same pins, different preservation sets: {graded[0]} vs {graded[1]}")
        print("The commits match and what counts as a regression does not, which is")
        print("two benchmarks under one name -- the case the fingerprint missed.")
        return 1
    if not all(graded):
        print("one of these reports predates the graded-set digest, so whether the")
        print("preservation sets matched cannot be checked. Treat with suspicion.")
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


def regrade(report: Path, bundles: Path, out: Path) -> int:
    """Grade every preserved candidate again, and say what moved.

    This is the whole point of D54. A run kept as a patch against a recorded
    base can be graded again when the grader changes; twelve candidates that
    went with their TemporaryDirectory could not, which is why a null published
    from a defective grader is still uncheckable.

    It was needed within four hours of the first paid sweep. An agent's editable
    install broke a dependency for every task that ran after it, and twelve runs
    were scored against agents that had in fact solved their tasks.
    """
    import tempfile

    from .bundle import record_grade
    from .live import grade_patch
    from .mined import load as load_mined

    tasks = {t.name: t for t in load_mined()}
    data = json.loads(report.read_text(encoding="utf-8"))
    moved = []
    for row in data["runs"]:
        directory = bundles / Path(row["bundle"]).name
        if not directory.exists():
            print(f"  missing bundle for {row['task']}: {directory}")
            return 1
        patch = (directory / "patch.diff").read_bytes().decode("utf-8")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            graded = grade_patch(tasks[row["task"]], patch, Path(tmp) / "court")
        was = row["outcome"]
        if was != graded.outcome:
            moved.append((row["task"], was, graded.outcome))
            print(f"  {row['task']:<26}{was:<11}-> {graded.outcome}", flush=True)
            # Both records are kept. What the grader said at the time is how the
            # contamination is visible at all; overwriting it would erase the
            # evidence that the first answer was wrong.
            first = directory / "grade.as-run.json"
            if not first.exists():
                first.write_bytes((directory / "grade.json").read_bytes())
            record_grade(directory, graded)
        row["outcome"] = graded.outcome
        row["resolved"] = graded.resolved
        row["note"] = graded.detail

    data["score"] = score(data["runs"], data["seed"])
    # The bands are derived too. Leaving them stale would publish a report whose
    # table disagrees with its own headline, which is worse than not having one.
    data["bands"] = bands_of(data["runs"],
                             {n: (t.source or {}).get("gold_lines", 0)
                              for n, t in tasks.items()})
    data["regraded_from"] = str(report)
    out.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print()
    print(f"{len(moved)} of {len(data['runs'])} grade(s) changed. wrote {out}")
    return show(out)


def done_already(journal: Path) -> dict[tuple[str, str], int]:
    """How many replicates of each task *and arm* are already on disk.

    A long unattended sweep that keeps its results only in memory loses all of
    them to one crash at run eighty. Every run is appended the moment it
    finishes, and a restart picks up where the file ends.
    """
    if not journal.exists():
        return {}
    counted: dict[tuple[str, str], int] = {}
    for row in read_journal(journal):
        key = (row["task"], row["arm"])
        counted[key] = counted.get(key, 0) + 1
    return counted


def read_journal(journal: Path) -> list[dict]:
    if not journal.exists():
        return []
    return [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def run_baseline(tasks: list[Task], arms: list[str], model: str, replicates: int,
                 bundles: Path, seed: int, journal: Path, effort: str = "",
                 budget: float = 0.0, expect: str = "") -> list[dict]:
    shuffler = random.Random(seed)
    already = done_already(journal)
    if already:
        print(f"resuming: {sum(already.values())} run(s) already recorded")

    for task in tasks:
        # Both arms of a task, back to back, before the next task. A sweep that
        # runs one arm to completion and then the other lets anything that
        # drifts in between land entirely on one side: that is exactly what
        # happened when an agent broke the machine partway through pass B, and
        # every affected run was in the same arm because there was only one.
        for which in arm_order(arms, shuffler):
            for replicate in range(replicates):
                if already.get((task.name, which), 0) > replicate:
                    continue
                run = once(task, which, model, bundles, effort, budget)
                row = run.__dict__
                # Appended before anything else can fail. The bundle is already
                # on disk by this point; this is the row that makes it countable.
                with journal.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(row) + "\n")
                wrong = bool(expect) and not _used(run, expect)
                print(f"  {task.name:<26}{which:<9}"
                      f"{'resolved' if run.resolved else run.outcome:<11}"
                      f"{run.turns:>3} turns {run.seconds:>5.0f}s ${run.cost:.2f}"
                      + ("   MODEL MISMATCH" if wrong else ""), flush=True)
                if wrong:
                    # An unattended sweep that keeps going here spends the whole
                    # night measuring a model nobody asked for. The journal is
                    # already written, so stopping costs only what is left.
                    raise SystemExit(
                        f"stopping: asked for {expect}, the bundle manifest says "
                        f"otherwise. {sum(already.values()) if already else 0} prior "
                        f"run(s) kept in {journal}.")
    return read_journal(journal)


def _used(run: Run, expect: str) -> bool:
    """Whether the run's bundle records the model that was asked for.

    An arm labelled present and absent is E4; a model labelled present and
    absent is the same defect one field over, and an overnight sweep is exactly
    where it would go unnoticed until the bill arrived.
    """
    if not run.bundle:
        return True
    manifest = Path(run.bundle) / "manifest.json"
    if not manifest.exists():
        return True
    return expect in json.loads(manifest.read_text(encoding="utf-8")).get("model", "")


def main(argv: list[str]) -> int:
    def option(flag, default):
        return argv[argv.index(flag) + 1] if flag in argv else default

    if "--regrade" in argv:
        rest = [a for a in argv[argv.index("--regrade") + 1:] if not a.startswith("-")]
        if len(rest) < 2:
            print("usage: --regrade REPORT.json BUNDLES_DIR [--out corrected.json]")
            return 1
        return regrade(Path(rest[0]), Path(rest[1]),
                       Path(option("--out", "regraded.json")))
    if "--show" in argv:
        return show(Path(option("--show", "baseline.json")))
    if "--compare" in argv:
        rest = [a for a in argv[argv.index("--compare") + 1:] if not a.startswith("-")]
        if len(rest) < 2:
            print(__doc__)
            return 1
        return compare(Path(rest[0]), Path(rest[1]))

    model = option("--model", "")
    arms = [a.strip() for a in option("--arm", "vanilla").split(",") if a.strip()]
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
    unknown = [a for a in arms if a not in ARMS]
    if unknown:
        print(f"unknown arm(s) {', '.join(unknown)}; one of {', '.join(ARMS)}")
        return 1

    bundles = Path(option("--bundles", "runs"))
    print(f"model    {model}")
    print(f"corpus   {corpus_fingerprint(lock)}  ({len(tasks)} tasks)")
    print(f"seed     {seed}   arm(s) {', '.join(arms)}, {replicates} replicate(s) each")
    print(f"bundles  {bundles}")
    print()

    out = Path(option("--out", "baseline.json"))
    journal = out.with_suffix(".jsonl")
    effort = option("--effort", "")
    budget = float(option("--budget", "0") or 0)
    print(f"effort   {effort or 'default'}   per-run budget "
          f"{('$' + format(budget, '.2f')) if budget else 'none'}")
    print(f"journal  {journal}   (every run appended as it finishes)")
    print()

    rows = run_baseline(tasks, arms, model, replicates, bundles, seed, journal,
                        effort, budget, expect=option("--expect", ""))
    report = {
        "model": model,
        "arm": ",".join(arms),
        "corpus": corpus_fingerprint(lock),
        "graded": graded_fingerprint(tasks),
        "seed": seed,
        "environment": environment(),
        "score": score(rows, seed),
        "bands": bands_of(rows, {t.name: (t.source or {}).get("gold_lines", 0)
                                 for t in tasks}),
        "effort": effort,
        "runs": rows,
    }
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
