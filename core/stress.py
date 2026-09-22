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
SWE-bench Verified instances admit a wrong-but-passing patch**.

**This project's own ledger has now been asked, and it disagreed.** Across B3
and B4 — 22 runs on 16 real tasks, sonnet and opus — exactly **one** verdict
came back `VACUOUS`, and it did not replicate when the other model was given the
identical task. 0 of 14 on B4. Whatever the 46% describes, it is not what this
corpus produces, and the honest reading is that the effect is rare here rather
than that the literature is wrong: these are well-specified tasks from
well-maintained repositories, which is not where sloppy evidence would be
expected to live. Six of those fourteen also had a base tree so broadly red that
`VACUOUS` was close to unreachable by construction.

So this module is kept for what it demonstrably does — it caught the one real
case, and the reproduction and `failed_before` it computes on the same run are
used by §5.13 — and not for a frequency it has not shown. See
`results/b4-discriminate/findings.md`.

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
    already_green = set(ledger.passed_before)
    for need, command in sorted(config.commands.items()):
        carried = _tests_the_task_touched(ledger)
        stamp = _inputs_stamp(ledger.root, ledger.base, command, carried)
        # Cached only while the inputs it was computed from are unchanged. The
        # base commit does not move, which is what the cache was justified by -
        # but the tests carried onto it do, and they are the other half of the
        # question being asked.
        if need in verdicts and ledger.discrimination_inputs.get(need) == stamp:
            continue
        if not _passing(ledger):
            # Nothing claims this check passed, so there is nothing to question.
            continue
        found = on_the_old_tree(ledger.root, ledger.base, _with_outcomes(command),
                                carry=carried)
        ledger.discrimination_inputs[need] = stamp
        if found is None:
            verdicts[need] = UNCHECKABLE
            continue
        passed_before, output = found
        verdicts[need] = VACUOUS if passed_before else DISCRIMINATES
        # Which tests were seen *passing* back there, by name. `already_red`
        # below is the mirror of this, and having only the red half is what let
        # `assumptions.vacuous_tests` read "absent from the failures" as "passed"
        # - a test that was skipped or never reached is absent too.
        already_green |= {m.group(1).replace("\\", "/") for m in PASSED_LINE.finditer(output)}
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
    # Assigned rather than returned: every caller unpacks a pair, and the
    # green half is a cache like the other two rather than a third answer.
    ledger.passed_before = sorted(already_green)
    return verdicts, sorted(already_red)


def _inputs_stamp(root: Path, base: str, command: str, carried: tuple[str, ...]) -> str:
    """Everything the old-tree answer depended on, as one string.

    The base commit and the command are fixed text; the carried test files are
    not, so they go in by *content*. `tree_hash` is the same fingerprint
    evidence freshness uses, for the same reason - identical bytes hash
    identically, so reformatting a test does not invalidate an answer that still
    holds.
    """
    from .evidence import tree_hash

    return f"{base}|{command}|{tree_hash(root, carried) if carried else '-'}"


def _with_outcomes(command: str) -> str:
    """Ask pytest to name every outcome, when the declared command is pytest.

    Left exactly as declared for anything else. The base-tree run is where
    `passed_before` comes from, and a pass pytest never printed is a pass
    nobody can claim.
    """
    tokens = command.split()
    if not any(t.endswith("pytest") for t in tokens) or "-rA" in tokens:
        return command
    return command + " -rA"


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


def _passing(ledger) -> bool:
    """Does anything here claim the tests currently pass?

    **Not an exact match on the declared command.** That was the first version
    and it engaged on nothing: agents run their own invocation — measured, a
    live run produced `cd "C:\\...\\tmp" && PYTHONPATH="src" python -m pytest
    tests` — and never the bare declared string. The declared command is only
    run by `core/verify.py`, which fires *when the verdict is not yet VERIFIED*,
    so on a run that went well nothing ever recorded it and the whole check
    skipped itself. Two paid runs came back with an empty verdict before that
    was noticed.

    What the question actually needs is a claim that the tests pass *now*; the
    declared command is how the old tree gets asked the same thing, and it does
    not have to be the string the agent typed.

    **Fresh or stale, but not gone.** Requiring FRESH cost two of the sixteen
    B3 runs their whole answer. The question here is about the *base tree* and
    the *declared command*, and neither moves when the agent edits a file after
    running the tests — but that edit staled every passing record, so the gate
    closed and the run recorded no verdict, no `failed_before` and therefore no
    reproduction either. Measured on `click-9f9b149e`: the last passing record's
    tree is not the tree of its last record, so the tree moved underneath it.

    A stale record still *claims* the tests passed, which is the claim §5.10
    exists to question, and the staleness itself is already reported by the
    freshness machinery rather than needing to be enforced here. GONE is
    different: the files a record observed no longer exist, so there is no
    coherent claim left to question.
    """
    from .evidence import Freshness, Kind, Result

    return any(e.kind in (Kind.TEST, Kind.SUITE) and e.result is Result.PASS
               and e.freshness(ledger.root) in (Freshness.FRESH, Freshness.STALE)
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


CONFIRMED = "targeted reproduction"
CONFIRM_LIMIT = 12

# pytest's own summary line for a test that ran and passed. Captured from
# `pytest -q -rA` on 3.13 rather than remembered; the id is the whole token, so
# parametrised ids like `test_x[case-1]` come through intact.
PASSED_LINE = re.compile(r"^PASSED\s+(\S+)", re.MULTILINE)

# Stopping early is the right default for a developer and the wrong one for a
# question about several named tests, so it is dropped for the confirmation run.
FAIL_FAST = re.compile(r"^(?:-x|--exitfirst|--maxfail(?:=.*)?)$")


def _targeted(command: str, root: Path, ids: tuple[str, ...]) -> str:
    """The declared command, narrowed to these node ids, or nothing.

    Appending ids is wrong whenever the command names a path of its own:
    `pytest tests` plus three ids runs the whole directory *and* the three,
    which is the suite again at a higher price. Substituting is right, and it is
    what the corpus needs - every task there declares `python -m pytest tests
    -q`, so an append-only version would have declined on all sixteen.

    A token is treated as a path only if it exists in the repository. That is
    what separates `tests` from a flag's value such as the `no:cacheprovider` in
    `-p no:cacheprovider`, which carries no slash and no extension and would
    otherwise look exactly as path-like. Anything unrecognised means the command
    is not understood, and an unrecognised command is declined rather than
    guessed at.
    """
    tokens = command.split()
    named = next((t for t in tokens if t.endswith("pytest")), "")
    if not named:
        return ""
    cut = tokens.index(named)
    flags, paths = [], []
    skip_value = False
    for token in tokens[cut + 1:]:
        if skip_value:
            skip_value = False    # `--maxfail 3` spends its value here
            continue
        if token.startswith("-"):
            if FAIL_FAST.match(token):
                skip_value = token == "--maxfail"
                continue      # see below
            flags.append(token)
        elif (root / token).exists():
            paths.append(token.replace("\\", "/").rstrip("/"))
        else:
            return ""
    # Never wider than what the project declared: every id has to sit inside a
    # path the command already covers.
    if paths and not all(any(i.replace("\\", "/").startswith(p) for p in paths) for i in ids):
        return ""
    # `-rA` asks pytest to name every outcome in the summary, and fail-fast is
    # dropped because the question here is what happened to *each* chosen id.
    # Both exist because this run's outcome used to be inferred rather than
    # read: see `confirm`.
    outcomes = [] if "-rA" in flags else ["-rA"]
    # Quoted, because this command is run through a shell and a pytest node id
    # is full of shell metacharacters. `test_converter_decorator[<lambda>0]` is
    # an ordinary parametrised id, and `<` is cmd.exe's input redirect: the
    # whole run died with "The system cannot find the file specified", exit 1,
    # zero tests executed.
    #
    # Exit 1 means "some test failed" and is allowed through, so the old code
    # then found no named failures and credited **every** selected id as a
    # passing reproduction. Measured on the real corpus: that is where 6 of 16
    # targeted reproductions came from, and the honest figure is 3.
    quoted = [f'"{i}"' if not (i.startswith('"') or '"' in i) else i for i in ids]
    return " ".join(tokens[:cut + 1] + flags + outcomes + quoted)


def _worth_confirming(ledger, red: list[str]) -> list[str]:
    """The red-on-base tests most likely to be about this change.

    Tests in files the task itself touched come first: those are the ones it
    wrote or edited, and a test the task wrote that was red before is the
    reproduction in the plainest sense.
    """
    mine = {p.replace("\\", "/") for p in ledger.touched}
    here = [r for r in red if r.split("::")[0].replace("\\", "/") in mine]
    return (here + [r for r in red if r not in here])[:CONFIRM_LIMIT]


def confirm(ledger) -> list:
    """Run the tests that were red on the base tree against the tree as it is.

    §5.13 asks for a test that was red before the change and is green after it.
    The runtime already learns the first half for free — `stress` runs the
    declared check against the base tree and the parsers read the failures out
    by name. The second half was left to chance: it waited for the agent to
    emit a *passing* record carrying the same node id, and `pytest -q` prints
    passes as dots. Measured on the B3 sweep, that path supplied **0 of 7**
    reproductions while the suite path supplied all seven, so the obligation was
    really the discrimination check wearing a second hat.

    So ask directly. These are node ids already known to have been red, run
    against the current tree — a handful of tests, not a suite. Whatever comes
    back passing is a genuine red-then-green reproduction, by name, whatever
    order the agent happened to work in.

    Returns evidence records, which is deliberately all it does: the records
    flow into `Ledger._reproduction`'s existing targeted path rather than adding
    a third way to satisfy the same obligation.
    """
    if any(d.get("what") == CONFIRMED for d in ledger.decisions):
        return []
    red = [r for r in ledger.failed_before if "::" in r]
    command = ledger.config.commands.get("tests", "")
    if not red or not command:
        return []
    chosen = _worth_confirming(ledger, red)
    run = _targeted(command, ledger.root, tuple(chosen))
    if not run:
        return []

    try:
        done = subprocess.run(run, shell=True, cwd=ledger.root, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return []

    output = (done.stdout or "") + (done.stderr or "")
    # 0 is everything passed, 1 is some test failed. Anything else - a usage
    # error, nothing collected, an internal error - means the question was not
    # answered, and an unanswered question must not read as a pass.
    #
    # The note comes *after* this, not before. Recording it first meant a usage
    # error spent the one attempt: the decision suppresses any later try, so a
    # command that never ran a test permanently prevented one that would have.
    # A failed invocation is not an observation and must not be filed as one.
    if done.returncode not in (0, 1):
        return []
    ledger.note(CONFIRMED, f"ran {len(chosen)} test(s) that were red on {ledger.base[:8]}")

    # Read the passes; never infer them.
    #
    # This used to subtract the ids pytest named as failing and call the
    # remainder green, on the reasoning that "the ids were chosen here, so what
    # ran is known". That reasoning is false in every direction that matters. An
    # audit reproduced two of them: under `-x` a later selected test never
    # executes and was still emitted as a passing reproduction, and a test
    # pytest *skipped* was emitted as passing too. Deselection, a collection
    # error and a crash mid-run do the same thing. Selection is not execution,
    # and execution is not success.
    #
    # `-rA` makes pytest state each outcome, and only an id it names as PASSED
    # is credited. Read from a real run rather than assumed: SKIPPED lines carry
    # no node id at all - `SKIPPED [1] tests\test_a.py:9: reason` - so a rule
    # that subtracted non-passes could not have seen them even in principle,
    # while a rule that requires a positive PASSED line is unaffected.
    from .evidence import Evidence, Kind, Result, source_files, tree_hash

    passed = {m.group(1).replace("\\", "/") for m in PASSED_LINE.finditer(output)}
    green = [i for i in chosen if i.replace("\\", "/") in passed]
    if not green:
        return []
    observed = source_files(ledger.root)
    tree = tree_hash(ledger.root, observed)
    return [Evidence(kind=Kind.TEST, identity=i, result=Result.PASS, observed=observed,
                     tree=tree, scope="source", command=run, counted=True,
                     detail=f"red on {ledger.base[:8]}, passes on the tree as it is")
            for i in green]
