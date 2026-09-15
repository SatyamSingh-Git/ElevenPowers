"""Running the project's own checks the other way round.

A check that passes is two facts short of being evidence. It has to be *fresh* —
`evidence.py` answers that — and it has to be able to **fail**. A test that
would have passed before the change was made proves nothing about the change,
and today the runtime would call it `VERIFIED` all the same.

This is PLAN §5.0 turned on the product instead of on the test suite:

    forward       the declared check passes on the tree as it stands
    adversarial   the same check, run against the tree as it was before this
                  task began, must NOT pass

Both, or the record is decoration. Measured elsewhere, **46% of agent
validation evidence carries no bug-discriminating information**, and **77% of
SWE-bench Verified instances admit a wrong-but-passing patch**. This project's
own ledger has never been asked the question.

**It reports; it does not refuse.** A check found undiscriminating leaves the
verdict exactly where it was. §5.12: detection and intervention are separately
justified, and this project has already paid once for the other choice — the
gate blocked 75 percent of runs on work that was already correct before M1 cut
it to 12. Naming a weak check costs nothing and cannot destroy correct work;
blocking on one has to earn its cost with evidence that does not exist yet.

**Only declared commands are run.** Same rule as `core/verify.py`, for the same
reason and one more: a recorded command is a shell line from somebody else's
workspace — the preserved corpus is full of `cd "C:\\...\\tmp6wszojx2" && ...` —
and re-running it somewhere new is at best meaningless. What a project declared
about itself is relative, stable and sanctioned.

**The user's working tree is never touched.** The adversarial run happens in a
detached `git worktree` built from the base commit, and the answer is cached in
the ledger: the base does not move during a task, so each declared command is
run this way once, not once per stop.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

TIMEOUT = 300

# What the check concluded, stored on the evidence record. Absent means nobody
# asked — which is the honest default and distinct from "asked, and it could
# not fail".
UNKNOWN, DISCRIMINATES, VACUOUS, UNCHECKABLE = "", "yes", "no", "n/a"


def _git(root: Path, *args: str, timeout: int = 30) -> str | None:
    try:
        done = subprocess.run(["git", *args], cwd=root, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def base_commit(root: Path) -> str:
    """The commit a task starts from, recorded before anything is edited.

    HEAD at the moment the task opens, not at the moment the question is asked:
    an agent that commits mid-task would otherwise move the thing its work is
    being compared against, and the check would compare the change to itself.
    """
    return _git(root, "rev-parse", "HEAD") or ""


def before_the_change(root: Path, commit: str, command: str,
                      timeout: int = TIMEOUT) -> bool | None:
    """Did `command` already pass before this task began?

    True means it passed without the change and therefore could not have been
    testing it. None means the question could not be asked — no git, no such
    commit, a worktree that would not build — which is reported as unknown
    rather than guessed either way.
    """
    if not commit:
        return None
    hold = Path(tempfile.mkdtemp(prefix="ep-before-"))
    tree = hold / "tree"
    try:
        if _git(root, "worktree", "add", "--detach", str(tree), commit, timeout=120) is None:
            return None
        try:
            done = subprocess.run(command, shell=True, cwd=tree, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace",
                                  timeout=timeout)
        except (OSError, subprocess.SubprocessError):
            return None
        return done.returncode == 0
    finally:
        _git(root, "worktree", "remove", "--force", str(tree), timeout=60)
        # `ignore_errors` because a test run can leave a file the OS still holds
        # open, and failing to tidy a temporary directory must never be the
        # reason a task cannot finish. eval/mine.py learned this first; the
        # live harness had to learn it again after a cleanup crash ended a paid
        # sweep.
        shutil.rmtree(hold, ignore_errors=True)


def stress(ledger) -> dict[str, str]:
    """Run every declared check the other way round, once per task.

    Returns the verdict per need. Cached on the ledger, because the base commit
    does not move while a task runs, so the answer cannot change either.
    """
    config = ledger.config
    if not config.commands or not ledger.base:
        return dict(ledger.discrimination)

    verdicts = dict(ledger.discrimination)
    for need, command in sorted(config.commands.items()):
        if need in verdicts:
            continue
        if not _passing(ledger, need):
            # Nothing claims this check passed, so there is nothing to question.
            continue
        passed_before = before_the_change(ledger.root, ledger.base, command)
        verdicts[need] = (UNCHECKABLE if passed_before is None
                          else VACUOUS if passed_before else DISCRIMINATES)
    return verdicts


def _passing(ledger, need: str) -> bool:
    """Is there a fresh passing record for the command this need declares?"""
    command = ledger.config.command_for(need)
    from .evidence import Freshness, Result

    return any(e.result is Result.PASS and e.command == command
               and e.freshness(ledger.root) is Freshness.FRESH
               for e in ledger.evidence)


def wording(verdicts: dict[str, str]) -> list[str]:
    """What to tell the user, for the needs where it is worth saying anything."""
    lines = []
    for need, verdict in sorted(verdicts.items()):
        if verdict == VACUOUS:
            lines.append(f"{need}: this check passes without your change, so it is "
                         f"not evidence the change works")
        elif verdict == UNCHECKABLE:
            lines.append(f"{need}: could not be run against the tree as it was, "
                         f"so whether it discriminates is unknown")
    return lines
