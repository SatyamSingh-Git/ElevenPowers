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

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

TIMEOUT = 300

# `ERROR tests/test_new.py` — a whole file that would not collect on the old
# tree. Kept alongside node ids in the same set because it is the same fact,
# and matched by prefix because it carries no node.
COLLECT_ERROR = re.compile(r"^ERROR\s+(\S+\.py)\b", re.MULTILINE)

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


def on_the_old_tree(root: Path, commit: str, command: str,
                    timeout: int = TIMEOUT,
                    carry: tuple[str, ...] = ()) -> tuple[bool, str] | None:
    """Run `command` against the tree as it was, and keep what it said.

    The output matters as much as the exit code, and for a different question.
    The code answers §5.10 — *could this check have failed?* The output answers
    §5.13 — *which individual tests were already red back there?* — and a test
    that was red before and is green now is a reproduction, whatever order the
    agent happened to work in.

    One run, both answers. Asking them separately would mean building the
    worktree and running the suite twice for facts that arrive together.

    None means the question could not be asked: no commit, no worktree, a
    command that would not start. Unknown, never a guess.
    """
    if not commit:
        return None
    hold = Path(tempfile.mkdtemp(prefix="ep-before-"))
    tree = hold / "tree"
    try:
        if _git(root, "worktree", "add", "--detach", str(tree), commit, timeout=120) is None:
            return None
        # The old *source*, with the new *tests* laid over it. Without this the
        # question cannot be asked at all: a test the agent wrote a minute ago
        # is not in the base commit, so the old tree could never run it, and
        # every check would come back "passed before" by construction. Carrying
        # the tests across is exactly what a reviewer does by hand — keep the
        # fix out, keep the test in, and see what happens.
        for rel in carry:
            source = root / rel
            if not source.is_file():
                continue
            target = tree / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        try:
            done = subprocess.run(command, shell=True, cwd=tree, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace",
                                  timeout=timeout)
        except (OSError, subprocess.SubprocessError):
            return None
        return done.returncode == 0, (done.stdout or "") + (done.stderr or "")
    finally:
        _git(root, "worktree", "remove", "--force", str(tree), timeout=60)
        # `ignore_errors` because a test run can leave a file the OS still holds
        # open, and failing to tidy a temporary directory must never be the
        # reason a task cannot finish. eval/mine.py learned this first; the
        # live harness had to learn it again after a cleanup crash ended a paid
        # sweep.
        shutil.rmtree(hold, ignore_errors=True)


def stress(ledger) -> tuple[dict[str, str], list[str]]:
    """Run every declared check the other way round, once per task.

    Returns the verdict per need, and every test identity that was **already
    failing** on the old tree. The second is what makes §5.13's reproduction
    obligation computable instead of merely observable: a test red back there
    and green now is a reproduction, and the agent does not have to have run it
    in that order for it to be true.

    Both are cached on the ledger. The base commit does not move while a task
    runs, so neither answer can change.
    """
    from .evidence import Kind, Result
    from .parsers import parse

    config = ledger.config
    if not config.commands or not ledger.base:
        return dict(ledger.discrimination), list(ledger.failed_before)

    verdicts = dict(ledger.discrimination)
    already_red = set(ledger.failed_before)
    for need, command in sorted(config.commands.items()):
        if need in verdicts:
            continue
        if not _passing(ledger, need):
            # Nothing claims this check passed, so there is nothing to question.
            continue
        found = on_the_old_tree(ledger.root, ledger.base, command,
                                carry=_tests_the_task_touched(ledger))
        if found is None:
            verdicts[need] = UNCHECKABLE
            continue
        passed_before, output = found
        verdicts[need] = VACUOUS if passed_before else DISCRIMINATES
        # The runtime's own parsers, on the old tree's output. Whatever it can
        # read as a failing test there is a test the change made pass.
        already_red |= {r.identity for r in parse(command, output, 0 if passed_before else 1,
                                                  ledger.root)
                        if r.kind is Kind.TEST and r.result is not Result.PASS}
        # And the files that could not even be collected. This is the *common*
        # case, not an edge one: a test for behaviour the fix introduces cannot
        # import on the old tree, so pytest reports `ERROR tests/test_new.py`
        # with no node id at all and the parsers above see nothing. Matching by
        # file is what makes the obligation dischargeable for the shape of
        # change it exists to describe.
        already_red |= set(COLLECT_ERROR.findall(output))
    return verdicts, sorted(already_red)


def _tests_the_task_touched(ledger) -> tuple[str, ...]:
    """Test files this task wrote or edited, to lay over the old source.

    Tests only. Carrying a source file across would defeat the whole question —
    the point is the old behaviour meeting the new test. `surface.TEST_NAME` is
    the same rule the rest of the runtime uses to decide what looks like a test,
    so a project whose tests are named unusually is treated consistently
    everywhere rather than specially here.
    """
    from .surface import TEST_NAME

    return tuple(p for p in ledger.touched if TEST_NAME.search(p))


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
