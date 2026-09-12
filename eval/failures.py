"""What went wrong, in categories decided by evidence, each citing its runs.

    python -m eval.failures runs/
    python -m eval.failures runs/ --category localised

A score says how often the agent succeeded. It says nothing about what to build
next, and this project has twice drawn a conclusion about *why* a run failed
from a story rather than from the run: once diagnosing a null from the agent's
own test without reading the answer key, once deciding that failures needed
information the runtime could not reach when six of seven were reachable.

So every category here is decided by something in the bundle — a grade outcome,
a host field, the patch itself — and every category prints the bundles it came
from. A category you cannot open is a category you are about to tell a story
about.

**The split that matters is the last one.** A candidate that failed while
touching the files the maintainer touched found the right code and wrote the
wrong change; one that touched none of them never found it. Those are different
problems with different fixes, and nothing in this project has distinguished
them before.

**A caution that belongs in the output, not the footnotes.** At fifteen tasks
most categories hold one or two runs. The job at this size is to say which
failures happened and let you read them, not to report proportions anyone should
act on.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from .bundle import read

# Ordered: the first matching category wins, so a run that timed out is not also
# counted as one that changed nothing. Harness problems come first because they
# are not evidence about the agent at all.
CATEGORIES = (
    ("setup", "the harness could not build or grade the run"),
    ("timeout", "the run hit its time limit"),
    ("host-error", "the host reported an error or an unfinished turn"),
    ("abstained", "the agent said it could not do the task"),
    ("no-patch", "the agent finished and changed nothing"),
    ("regressed", "the requested tests pass and something else broke"),
    ("localised", "wrong fix, but it edited the files the maintainer edited"),
    ("misplaced", "wrong fix, and it edited none of them"),
    ("resolved", "the requested tests pass and nothing else broke"),
)

TOUCHED = re.compile(r"^diff --git a/(\S+) b/", re.MULTILINE)


def touched(patch: str) -> set[str]:
    return set(TOUCHED.findall(patch))


def classify(bundle: dict) -> str:
    """One category per run, from the bundle and nothing else."""
    grade = bundle.get("grade") or {}
    answer = bundle.get("answer") or {}
    manifest = bundle.get("manifest") or {}
    outcome = grade.get("outcome", "")

    if outcome == "setup":
        return "setup"
    if outcome == "timeout":
        return "timeout"
    if answer.get("is_error") or answer.get("api_error_status") or (
            answer.get("terminal_reason") not in (None, "completed")):
        return "host-error"
    if grade.get("resolved"):
        return "resolved"
    if outcome == "regressed":
        return "regressed"
    if not bundle.get("patch", "").strip():
        return "no-patch"

    gold = set(manifest.get("gold") or [])
    if not gold:
        # Without the maintainer's file list there is no way to tell the two
        # apart, and guessing would be exactly what this module exists to stop.
        return "unattributed"
    return "localised" if touched(bundle["patch"]) & gold else "misplaced"


def collect(where: Path) -> dict[str, list[tuple[str, dict]]]:
    out: dict[str, list[tuple[str, dict]]] = {}
    for directory in sorted(p for p in where.iterdir() if (p / "manifest.json").exists()):
        bundle = read(directory)
        out.setdefault(classify(bundle), []).append((directory.name, bundle))
    return out


def flaky(found: dict[str, list[tuple[str, dict]]]) -> list[str]:
    """Tasks whose replicates disagree with each other.

    A task that resolves twice and fails once is telling you about variance, not
    about capability, and reading its one failure as a finding is how a noise
    floor becomes a diagnosis.
    """
    outcomes: dict[str, set[str]] = {}
    for category, runs in found.items():
        for _, bundle in runs:
            task = (bundle.get("manifest") or {}).get("task", "?")
            outcomes.setdefault(task, set()).add(category)
    return sorted(task for task, kinds in outcomes.items() if len(kinds) > 1)


def report(where: Path, only: str = "") -> int:
    if not where.is_dir():
        print(f"no bundles at {where}")
        return 1
    found = collect(where)
    if not found:
        print(f"no bundles at {where}")
        return 1

    total = sum(len(v) for v in found.values())
    print(f"{total} run(s) from {where}")
    print()
    print(f"{'category':<14}{'runs':>5}  what it means")
    known = dict(CATEGORIES)
    for name, meaning in CATEGORIES:
        if name in found:
            print(f"{name:<14}{len(found[name]):>5}  {meaning}")
    for name, runs in sorted(found.items()):
        if name not in known:
            print(f"{name:<14}{len(runs):>5}  no gold file list in the bundle")

    agent = sum(len(v) for k, v in found.items() if k not in ("setup", "timeout", "host-error"))
    harness = total - agent
    if harness:
        print()
        print(f"{harness} of {total} run(s) failed as harness or host, not as the agent.")
        print("Those are excluded from any statement about capability.")

    print()
    for name, runs in sorted(found.items(), key=lambda kv: (kv[0] not in known, kv[0])):
        if only and name != only:
            continue
        print(f"{name} ({len(runs)})")
        for directory, bundle in runs:
            grade = bundle.get("grade") or {}
            detail = grade.get("detail", "")
            print(f"  {directory}")
            if detail:
                print(f"      {detail[:120]}")
        print()

    unstable = flaky(found)
    if unstable:
        print(f"{len(unstable)} task(s) landed in more than one category across their")
        print(f"replicates: {', '.join(unstable[:6])}")
        print("Their single failures are variance until more replicates say otherwise.")

    if total < 30:
        print()
        print(f"{total} runs is a listing, not a distribution. Read the bundles; do not")
        print("quote the proportions.")
    return 0


def main(argv: list[str]) -> int:
    def option(flag, default):
        return argv[argv.index(flag) + 1] if flag in argv else default

    rest = [a for a in argv[1:] if not a.startswith("-")]
    if not rest:
        print(__doc__)
        return 1
    return report(Path(rest[0]), option("--category", ""))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
