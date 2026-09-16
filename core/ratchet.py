"""Keeping the best state a task ever proved, so a later edit cannot lose it.

Measured elsewhere: **60-69% of coding-agent failures reach and edit the correct
functions and still produce a wrong patch**, and five documented cases produced
a patch identical to the reference solution mid-trajectory and then corrupted
it. All five were recovered by checkpointing the edits. PLAN §5.6 said the same
thing from the other side long before that paper: *a long attempt ends at its
latest patch, not its best.*

**What is borrowed** (`docs/research/build-on.md`, C0). The checkpoint store is
**Cline's** — snapshots in private refs, never touching the user's branch,
index, stash or working tree — and so is the **compare-and-swap restore that
refuses when HEAD has moved**. That refusal is the part that matters: the 2026
recoverability work found checkpoint-only recovery choosing an *ineligible*
source in every eligibility challenge while restoring bytes perfectly and
satisfying every final invariant, and concluded that **task success cannot
detect a bad recovery decision**. A paper named the gap; Cline had already
closed it.

**What is ours: when to snapshot.** Everyone else snapshots per step or per
edit, which is why the published cost of this intervention is *10 to 40 times
the test invocations*. This snapshots only when the ledger says the declared
checks are **green and fresh against the exact files they observed** — a state
`core/evidence.py` already computes on every edit and then throws away. The
expensive part of the idea is the part invalidation makes free.

**It offers; it does not restore.** Same rule as `core/stress.py` and for the
same reason (§5.12): a mechanism that changes the working tree on its own has to
earn that with evidence this project does not have. The end report names the
snapshot and prints the command. A person runs it.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

# Private, like Cline's: under `refs/` but outside `refs/heads` and `refs/tags`,
# so it never appears in `git branch`, `git tag`, `git log --all` or a push, and
# is not something the agent trips over while working.
NAMESPACE = "refs/elevenpowers/proven"


def _git(root: Path, *args: str, env: dict | None = None) -> str | None:
    try:
        done = subprocess.run(["git", *args], cwd=root, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=60, env={**os.environ, **(env or {})})
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def snapshot(root: Path, task: str, note: str) -> str | None:
    """Commit the working tree to a private ref, touching nothing the user owns.

    A temporary index rather than the repository's own: `git add -A` against
    `.git/index` would stage the agent's work as a side effect of observing it,
    and a runtime that changes what it is measuring is the defect this project
    keeps finding in other places.

    Untracked files are included deliberately. The test an agent just wrote is
    untracked and is exactly the thing worth keeping.
    """
    head = _git(root, "rev-parse", "HEAD")
    if head is None:
        return None
    with tempfile.TemporaryDirectory(prefix="ep-index-") as hold:
        env = {"GIT_INDEX_FILE": str(Path(hold) / "index")}
        if _git(root, "add", "-A", env=env) is None:
            return None
        tree = _git(root, "write-tree", env=env)
    if not tree:
        return None
    commit = _git(root, "commit-tree", tree, "-p", head, "-m", f"{task}: {note}")
    if not commit:
        return None
    # The ref carries the parent, so a restore can ask whether HEAD is still
    # where the snapshot was taken from without re-reading the commit.
    _git(root, "update-ref", f"{NAMESPACE}/{task}", commit)
    return commit


def proven(root: Path, task: str) -> str | None:
    """The last state this task proved, if there is one."""
    return _git(root, "rev-parse", "--verify", "--quiet", f"{NAMESPACE}/{task}")


def eligible(root: Path, commit: str) -> bool:
    """Is this snapshot still a suitable place to resume?

    Cline's compare-and-swap condition: the snapshot was taken as a child of a
    particular HEAD, and if HEAD has moved since then restoring it would undo
    whatever moved it. Bytes would restore perfectly and the result would be
    wrong, which is precisely the failure mode task success cannot see.
    """
    parent = _git(root, "rev-parse", f"{commit}^")
    head = _git(root, "rev-parse", "HEAD")
    return bool(parent and head and parent == head)


def differs(root: Path, commit: str) -> bool:
    """Does the working tree actually differ from the proven state?

    Without this the report would offer a snapshot of the tree the user is
    already looking at, which is noise dressed as a finding.
    """
    with tempfile.TemporaryDirectory(prefix="ep-index-") as hold:
        env = {"GIT_INDEX_FILE": str(Path(hold) / "index")}
        if _git(root, "add", "-A", env=env) is None:
            return False
        tree = _git(root, "write-tree", env=env)
    return bool(tree) and tree != _git(root, "rev-parse", f"{commit}^{{tree}}")


def offer(root: Path, task: str) -> str:
    """What to tell the user about the best state this task reached, if anything.

    Silent unless there is something to say: no snapshot, an unchanged tree, or
    a HEAD that has moved all produce nothing rather than a hedge.
    """
    commit = proven(root, task)
    if not commit or not differs(root, commit):
        return ""
    if not eligible(root, commit):
        return (f"a proven state exists ({commit[:10]}) but HEAD has moved since it was "
                f"taken, so restoring it would undo the commit that moved it")
    return (f"this task reached a state where the declared checks passed, and the tree "
            f"has changed since. To see what moved:\n"
            f"    git diff {commit[:10]}\n"
            f"  To restore it:\n"
            f"    git restore --source={commit[:10]} --worktree -- .")
