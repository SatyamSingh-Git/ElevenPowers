"""Would the sweep measure anything? Ask before paying to find out.

    python -m eval.rehearse --corpus E:/ep-corpus/prevalence.json --tasks 4

A sweep was launched on 2026-09-16, ran two tasks, cost $1.42 and measured
**nothing**: `stress` required an evidence record carrying the *declared*
command string, agents type their own invocation, and the declared string is
only run by `core/verify.py` when the verdict is not yet VERIFIED. Every
successful run therefore skipped the check entirely and recorded `{}`.

Sizing did not catch it. `eval/engagement` counted "any passing suite record"
at 100% while the code required "a record carrying the declared string" at 0% —
the wrong predicate, measured confidently.

What catches it is doing the thing for real without paying for an agent. This
seeds a real task at its real base commit, applies the **gold patch** as a
correct agent would, records a passing suite with an *agent-shaped* command, and
asks the runtime the question the sweep exists to ask. Everything except the
agent is genuine: the repository, the base, the fix, the declared command, the
worktree, the parsers.

**What a pass means and does not mean.** It means the measurement path is wired
end to end and a sweep would return verdicts rather than `{}`. It says nothing
about what those verdicts will be — a rehearsal where every task discriminates
is a rehearsal, not a result.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def rehearse(task, fix: str, hold: Path) -> dict:
    """One task, seeded and patched, put through the real check."""
    from core import stress
    from core.config import Config, save as save_config
    from core.evidence import Evidence, Kind, Result, source_files, tree_hash
    from core.ledger import Ledger
    from core.obligations import Claim
    from .live import _seed_git, _test_command, base_tree

    root = hold / task.name
    root.mkdir(parents=True, exist_ok=True)
    base_tree(task, root)
    _seed_git(root)

    command = _test_command(task)
    save_config(root, Config(profile="strict", commands={"tests": command}))
    base = stress.base_commit(root)
    if not base:
        return {"task": task.name, "why": "no base commit after seeding"}

    gold = subprocess.run(["git", "-C", task.source["repo"], "show", fix],
                          capture_output=True, timeout=180)
    applied = subprocess.run(["git", "-C", str(root), "apply", "--3way", "-"],
                             input=gold.stdout, capture_output=True, timeout=180)
    if applied.returncode != 0:
        return {"task": task.name, "why": "gold patch would not apply"}

    changed = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                             capture_output=True, text=True, timeout=60).stdout.split()
    touched = [p.replace("\\", "/") for p in changed if p.endswith(".py")]

    observed = source_files(root)
    # Deliberately NOT the declared string. That is the whole point: this is the
    # shape of command an agent actually runs, and matching it exactly is what
    # made a paid sweep measure nothing.
    record = Evidence(kind=Kind.SUITE, identity="python pytest", result=Result.PASS,
                      observed=observed, tree=tree_hash(root, observed), scope="source",
                      command=f'cd "{root}" && {command}',
                      passed=10, failed=0, counted=True)
    ledger = Ledger(root=root, task="rehearsal", claims=[Claim.BUG_FIXED],
                    evidence=[record], base=base, touched=touched)

    verdicts, red = stress.stress(ledger)
    ledger.discrimination, ledger.failed_before = verdicts, red
    return {
        "task": task.name,
        "verdict": verdicts.get("tests", "NOT ASKED"),
        "red_before": len(red),
        "tests_carried": len(stress._tests_the_task_touched(ledger)),
        "reproduced": ledger._reproduced_on_base() is not None,
    }


def report(corpus: Path, limit: int) -> int:
    from .mined import load as load_mined

    os.environ["EP_MINED"] = str(corpus)
    rows = {r["name"]: r for r in json.loads(corpus.read_text(encoding="utf-8"))}
    tasks = [t for t in load_mined() if t.name in rows][:limit]
    if not tasks:
        print(f"no tasks in {corpus}")
        return 1

    print(f"rehearsing {len(tasks)} task(s) from {corpus.name}, no agent, no cost\n")
    results = []
    with tempfile.TemporaryDirectory(prefix="ep-rehearse-") as tmp:
        for task in tasks:
            try:
                results.append(rehearse(task, rows[task.name]["fix"], Path(tmp)))
            except Exception as trouble:                      # noqa: BLE001
                results.append({"task": task.name, "why": f"{type(trouble).__name__}: {trouble}"})
            last = results[-1]
            if "why" in last:
                print(f"  {last['task']:24s} could not rehearse: {last['why']}")
            else:
                print(f"  {last['task']:24s} verdict={last['verdict']:4s} "
                      f"red_before={last['red_before']:3d} carried={last['tests_carried']} "
                      f"reproduced={last['reproduced']}")

    asked = [r for r in results if r.get("verdict") not in (None, "NOT ASKED")]
    print(f"\nthe check was asked on {len(asked)} of {len(results)}")
    if len(asked) < len(results):
        print("Some runs recorded no verdict at all. A sweep would spend money to")
        print("learn nothing, which has happened once already. Fix before paying.")
        return 1
    print("The measurement path is wired end to end: a sweep would return verdicts.")
    print("What those verdicts turn out to be is the sweep's business, not this one's.")
    return 0


def main(argv: list[str]) -> int:
    if "--corpus" not in argv:
        print(__doc__)
        return 1
    corpus = Path(argv[argv.index("--corpus") + 1])
    limit = int(argv[argv.index("--tasks") + 1]) if "--tasks" in argv else 4
    return report(corpus, limit)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
