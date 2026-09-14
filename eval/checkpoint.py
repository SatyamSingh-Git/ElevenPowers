"""Record the candidate at every proposed stop, and never interfere.

Installed as a `Stop` hook in **both** arms. It exports the patch as it stands
the moment the agent tries to finish, appends it to the workspace, and always
allows the stop.

Why this exists. A paired sweep compares final outcomes, and on this corpus the
final outcomes agree: twenty-three of twenty-five tasks, with the gate blocking
in four runs of fifty. Measuring at the end spends almost everything on tasks
where nothing could differ. The place the treatment actually acts is the moment
the agent proposes to stop, and nothing until now recorded what it was proposing
*at that moment* -- only what it had after being refused.

So the first question this makes answerable is the one Phase B-prime needs:
**how often is the first proposed candidate already correct?** An agent that
eventually succeeds in forty turns may well be wrong at turn fifteen, and that
is true on easy tasks too. It is a different quantity from the resolve rate and
it has never been measured here.

**Passive by construction.** Recording at a decision point is not neutral if the
recorder can change the decision, so this writes a file and exits zero. It is
installed in the plain arm as well, because an instrument present in one arm and
absent in the other is the difference between the arms -- which is E4, and this
project has paid for that lesson twice.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

RECORD = ".elevenpowers/checkpoints.jsonl"


def candidate(root: Path) -> str:
    """The patch as it stands, against the commit the workspace was seeded at."""
    base = subprocess.run(["git", "-c", "core.autocrlf=false", "-C", str(root),
                           "rev-list", "--max-parents=0", "HEAD"],
                          capture_output=True, timeout=30)
    first = (base.stdout or b"").decode("utf-8", "replace").split()
    if not first:
        return ""
    subprocess.run(["git", "-c", "core.autocrlf=false", "-C", str(root), "add", "-A"],
                   capture_output=True, timeout=30)
    done = subprocess.run(["git", "-c", "core.autocrlf=false", "-C", str(root),
                           "diff", "--binary", first[-1]],
                          capture_output=True, timeout=60)
    return done.stdout.decode("utf-8", "replace") if done.returncode == 0 else ""


def hook() -> int:
    # Whatever happens, the stop is allowed. A recorder that can fail a run is
    # not a recorder, it is an intervention with a bug.
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        root = Path(payload.get("cwd") or ".")
        # Before the journal is opened. Opening it creates the file, and the
        # very next thing this does is `git add -A`, so the recorder would
        # appear inside the candidate it is recording. The workspace excludes
        # `.elevenpowers/` anyway; a recorder that relies on that to stay out
        # of its own measurement is one configuration change from corrupting it.
        patch = candidate(root)
        record = root / RECORD
        record.parent.mkdir(parents=True, exist_ok=True)
        with record.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "at": time.time(),
                "session": payload.get("session_id", ""),
                "patch": patch,
            }) + "\n")
    except Exception:
        pass
    return 0




def grade(bundles: Path, corpus: Path) -> int:
    """How often was the first proposed candidate already correct?

    The question Phase B-prime is built on, and the one a final-outcome sweep
    cannot ask. An agent that resolves a task in forty turns may have proposed
    something wrong at turn fifteen; the gate acts there, and nothing until now
    recorded what was on the table at that moment.

    This is deliberately not a score for either arm. It is a prevalence: if the
    first candidate is almost always right, there is nothing for an intervention
    at the stop to repair, and the checkpoint experiment is not worth running on
    this corpus either.
    """
    import tempfile

    from .live import grade_patch
    from .task import Task

    tasks = {r["name"]: Task(name=r["name"], prompt=r["prompt"], files={}, hidden="",
                             why="", source=r)
             for r in json.loads(corpus.read_text(encoding="utf-8"))}

    print(f"{'run':<46}{'first':<11}{'final':<11}  moved")
    first_right = both = 0
    rows = []
    for d in sorted(bundles.iterdir()):
        record = d / "proposals.json"
        if not record.exists() or d.name.split("--")[0] not in tasks:
            continue
        proposals = json.loads(record.read_text(encoding="utf-8"))
        if not proposals:
            continue
        task = tasks[d.name.split("--")[0]]
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            early = grade_patch(task, proposals[0]["patch"], Path(tmp) / "first")
        final = json.loads((d / "grade.json").read_text(encoding="utf-8"))["outcome"]
        moved = "" if early.outcome == final else f"{early.outcome} -> {final}"
        print(f"{d.name[:44]:<46}{early.outcome:<11}{final:<11}  {moved}")
        rows.append((d.name, early.outcome, final, len(proposals)))
        first_right += early.outcome == "resolved"
        both += 1

    if not both:
        print(f"no proposals recorded under {bundles}")
        return 1
    print()
    print(f"{first_right} of {both} first proposals were already correct "
          f"({first_right / both:.0%})")
    repairs = sum(1 for _, e, f, _ in rows if e != "resolved" and f == "resolved")
    print(f"{repairs} run(s) proposed something wrong and ended correct")
    many = sum(1 for _, _, _, n in rows if n > 1)
    print(f"{many} run(s) proposed more than once")
    print()
    print("This is a prevalence, not a score for either arm. If the first")
    print("candidate is nearly always right there is nothing at the stop for an")
    print("intervention to repair, and the checkpoint experiment is not worth")
    print("running on this corpus either.")
    return 0


def main(argv: list[str]) -> int:
    if "--grade" in argv:
        where = argv.index("--grade") + 1
        corpus = argv[argv.index("--corpus") + 1] if "--corpus" in argv else "corpus.json"
        return grade(Path(argv[where]), Path(corpus))
    return hook()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
