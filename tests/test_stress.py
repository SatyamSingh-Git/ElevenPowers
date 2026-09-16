"""The adversarial direction, run against a real repository.

PLAN §5.0 says a check is evidence only once it has been run both ways, and
§5.10 says a check that could not have failed is not evidence at all. This is
that rule pointed at the product rather than at the test suite, so the tests
below are themselves a forward/adversarial pair:

    forward       a check that really does test the change is marked as
                  discriminating, and is NOT reported as weak
    adversarial   a check that passes on the old tree too is caught

A module that marked everything vacuous would pass the adversarial test alone;
one that marked nothing vacuous would pass the forward test alone. Either on its
own is indistinguishable from the feature being deleted.

A real `git init` rather than a mock, because the whole mechanism is
`git worktree add --detach`, and a mocked worktree would test nothing but the
mock.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from core import stress
from core.config import Config, save as save_config
from core.evidence import Evidence, Kind, Result, source_files, tree_hash
from core.ledger import Ledger
from core.obligations import Claim


def git(root, *args):
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, f"git {' '.join(args)}: {done.stderr}"
    return done.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    """A repository whose suite is green at HEAD, so the base really is green."""
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "probe@example.invalid")
    git(tmp_path, "config", "user.name", "probe")
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "tests" / "test_app.py").write_text(
        "import sys; sys.path.insert(0, 'src')\n"
        "from app import add\n\n"
        "def test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


SUITE = f'"{sys.executable}" -m pytest tests -q'
# No path of its own, so node ids can be appended without widening it back to
# the whole directory. `SUITE` names `tests` and deliberately cannot be.
NODES = f'"{sys.executable}" -m pytest -q'


def ledger_for(repo, command=SUITE):
    save_config(repo, Config(profile="guide", commands={"tests": command}))
    observed = source_files(repo)
    record = Evidence(
        kind=Kind.SUITE, identity="python pytest", result=Result.PASS,
        observed=observed, tree=tree_hash(repo, observed), scope="source",
        command=command, passed=1, failed=0, counted=True,
    )
    return Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                  evidence=[record], base=stress.base_commit(repo))


def test_the_base_commit_is_captured(repo):
    assert stress.base_commit(repo) == git(repo, "rev-parse", "HEAD")


def test_a_check_that_passed_before_the_change_is_caught(repo):
    """Adversarial. The suite is green at HEAD, so it cannot be testing anything new."""
    # the change first, then the suite record — the order an agent works in, and
    # the order that leaves the record FRESH against the tree it was run on
    (repo / "src" / "app.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
        encoding="utf-8")
    led = ledger_for(repo)
    verdicts, red = stress.stress(led)
    assert verdicts["tests"] == stress.VACUOUS
    assert red == [], "a suite green on the old tree reproduced nothing"
    assert "not evidence the change works" in " ".join(stress.wording(verdicts))


def test_a_check_that_really_tests_the_change_is_not_called_weak(repo):
    """Forward, and the control that stops this becoming `always vacuous`.

    The suite fails at the base commit and passes now, which is exactly what a
    reproduction looks like: red before, green after.
    """
    # a test for behaviour that does not exist yet, committed so the base has it
    (repo / "tests" / "test_new.py").write_text(
        "import sys; sys.path.insert(0, 'src')\n"
        "from app import mul\n\n"
        "def test_mul():\n    assert mul(2, 3) == 6\n",
        encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "failing test first")

    head = git(repo, "rev-parse", "HEAD")
    # now the fix, uncommitted, exactly as an agent would leave it
    (repo / "src" / "app.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
        encoding="utf-8")
    led = ledger_for(repo)
    assert led.base == head

    verdicts, red = stress.stress(led)
    assert verdicts["tests"] == stress.DISCRIMINATES
    assert stress.wording(verdicts) == [], "a good check must not be reported as weak"


def test_the_working_tree_is_never_touched(repo):
    """The adversarial run happens elsewhere, or it is not safe to run at all."""
    (repo / "src" / "app.py").write_text("def add(a, b):\n    return a + b\n# edited\n",
                                         encoding="utf-8")
    led = ledger_for(repo)
    before = (repo / "src" / "app.py").read_text(encoding="utf-8")
    stress.stress(led)
    assert (repo / "src" / "app.py").read_text(encoding="utf-8") == before
    assert git(repo, "rev-parse", "HEAD") == led.base
    assert "worktree" not in git(repo, "worktree", "list").replace(str(repo), "")


def test_no_repository_is_unknown_rather_than_a_guess(tmp_path):
    """Absence of an answer is its own answer, and must not read as either one."""
    assert stress.base_commit(tmp_path) == ""
    assert stress.on_the_old_tree(tmp_path, "", SUITE) is None


def test_nothing_is_run_for_a_need_with_no_passing_evidence(repo):
    """No claim that it passed means no question to ask, and no suite to run."""
    save_config(repo, Config(profile="guide", commands={"tests": SUITE}))
    led = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                 base=stress.base_commit(repo))
    assert stress.stress(led) == ({}, [])


def test_the_answer_is_cached_for_the_task(repo):
    """The base does not move while a task runs, so neither can the answer."""
    led = ledger_for(repo)
    led.discrimination = {"tests": stress.DISCRIMINATES}
    # a command that would fail loudly if it were actually run
    save_config(repo, Config(profile="guide", commands={"tests": "exit 1"}))
    led._config = None
    assert stress.stress(led)[0]["tests"] == stress.DISCRIMINATES


def test_an_undeclared_command_is_never_run(repo):
    """Same rule as core/verify.py: only what the project declared about itself."""
    led = ledger_for(repo)
    save_config(repo, Config(profile="guide", commands={}))
    led._config = None
    assert stress.stress(led) == ({}, [])


# --- C1: a reproduction the runtime computes rather than waits for ----------

def test_a_test_red_on_the_old_tree_is_reported_as_already_failing(repo):
    """Forward. The agent wrote the test AFTER the fix, which is ordinary.

    Nothing in the ledger records it ever failing, because it never ran red
    here. The old tree knows it did.
    """
    (repo / "tests" / "test_new.py").write_text(
        "import sys; sys.path.insert(0, 'src')\n"
        "from app import mul\n\n"
        "def test_mul():\n    assert mul(2, 3) == 6\n",
        encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "the failing test is part of the base")

    (repo / "src" / "app.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
        encoding="utf-8")
    led = ledger_for(repo)
    _, red = stress.stress(led)
    # No node id: the file could not be collected back there, because the
    # function the test imports is what the change introduced.
    assert red == ["tests/test_new.py"], red

    # And the obligation discharges on it, which is the whole feature.
    led.failed_before = red
    led.evidence.append(Evidence(
        kind=Kind.TEST, identity="tests/test_new.py::test_mul", result=Result.PASS,
        observed=source_files(repo), tree=tree_hash(repo, source_files(repo)),
        scope="source", command=SUITE))
    assert led._reproduced_on_base() is not None


def test_a_test_green_on_the_old_tree_reproduces_nothing(repo):
    """Adversarial, and the control that stops this becoming `everything counts`.

    A test that already passed before the change cannot be a reproduction of
    anything, however green it is now.
    """
    (repo / "src" / "app.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
        encoding="utf-8")
    led = ledger_for(repo)
    _, red = stress.stress(led)
    assert red == []

    # And a green test cannot borrow a reproduction it never had, even with a
    # fresh passing record sitting right there.
    led.failed_before = red
    led.evidence.append(Evidence(
        kind=Kind.TEST, identity="tests/test_app.py::test_add", result=Result.PASS,
        observed=source_files(repo), tree=tree_hash(repo, source_files(repo)),
        scope="source", command=SUITE))
    assert led._reproduced_on_base() is None


def test_a_suite_red_on_the_old_tree_is_a_reproduction_too(repo):
    """The common case, and the one a node-only version missed.

    The parsers record individual nodes mainly when they FAIL: across every
    preserved ledger, 1,256 failing test records against four passing ones.
    A reproduction that only matched node identities engaged on 1.4% of saved
    runs, which is how measuring the engagement rate before spending is supposed
    to work.
    """
    (repo / "tests" / "test_new.py").write_text(
        "import sys; sys.path.insert(0, 'src')\n"
        "from app import mul\n\n"
        "def test_mul():\n    assert mul(2, 3) == 6\n",
        encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "failing test is part of the base")
    (repo / "src" / "app.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
        encoding="utf-8")

    led = ledger_for(repo)
    led.discrimination, led.failed_before = stress.stress(led)
    assert led.discrimination["tests"] == stress.DISCRIMINATES
    # no TEST record at all - only the suite-level pass the fixture carries
    assert not [e for e in led.evidence if e.kind is Kind.TEST]
    assert led._reproduced_on_base() is not None


def test_a_suite_green_on_the_old_tree_is_not_a_reproduction(repo):
    """The control. A vacuous suite must not become proof of a fix."""
    (repo / "src" / "app.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
        encoding="utf-8")
    led = ledger_for(repo)
    led.discrimination, led.failed_before = stress.stress(led)
    assert led.discrimination["tests"] == stress.VACUOUS
    assert led._reproduced_on_base() is None


def test_a_test_written_after_the_fix_is_carried_to_the_old_source(repo):
    """The case the base worktree could not see at all.

    An agent fixes the bug and *then* writes a test. That test is uncommitted,
    so a worktree built from the base commit does not contain it, and the check
    would come back "passed before" by construction — an answer determined by
    the harness rather than by the work. Carrying the test across is what a
    reviewer does by hand: keep the fix out, keep the test in.
    """
    (repo / "src" / "app.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
        encoding="utf-8")
    (repo / "tests" / "test_new.py").write_text(
        "import sys; sys.path.insert(0, 'src')\n"
        "from app import mul\n\n"
        "def test_mul():\n    assert mul(2, 3) == 6\n",
        encoding="utf-8")

    led = ledger_for(repo)
    led.touched = ["src/app.py", "tests/test_new.py"]
    verdicts, red = stress.stress(led)

    assert verdicts["tests"] == stress.DISCRIMINATES, \
        "the new test must be run against the old source, not left behind"
    assert red == ["tests/test_new.py"]


def test_only_tests_are_carried_across(repo):
    """Adversarial. Carrying the source too would answer the opposite question.

    With `src/app.py` laid over the old tree there is no old behaviour left to
    fail against, and every check would look discriminating.
    """
    (repo / "src" / "app.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
        encoding="utf-8")
    led = ledger_for(repo)
    led.touched = ["src/app.py"]
    assert stress._tests_the_task_touched(led) == ()
    verdicts, _ = stress.stress(led)
    assert verdicts["tests"] == stress.VACUOUS, "the fix must not be carried over"


def test_it_engages_on_the_agents_own_command_not_the_declared_string(repo):
    """The defect that made two paid runs measure nothing.

    `_passing` matched the declared command exactly. Agents never type it — a
    live run recorded the agent typed a `cd ... && PYTHONPATH=... pytest` line of its own,
    and the declared string is only ever run by `core/verify.py`, which
    fires when the verdict is NOT yet verified. So a run that went well recorded
    nothing matching, and the whole check skipped itself and returned `{}`.
    """
    (repo / "src" / "app.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
        encoding="utf-8")
    (repo / "tests" / "test_new.py").write_text(
        "import sys; sys.path.insert(0, 'src')\n"
        "from app import mul\n\n"
        "def test_mul():\n    assert mul(2, 3) == 6\n",
        encoding="utf-8")

    led = ledger_for(repo)
    led.touched = ["src/app.py", "tests/test_new.py"]
    # the agent's own invocation: same suite, different string entirely
    led.evidence[0].command = f'cd "{repo}" && PYTHONPATH="src" {SUITE}'

    verdicts, red = stress.stress(led)
    assert verdicts, "engaged on nothing, which is what two paid runs measured"
    assert verdicts["tests"] == stress.DISCRIMINATES

    # The same exact-match lived a second time in `_reproduced_on_base`, and a
    # rehearsal on a real corpus task is what surfaced it: the verdict said
    # DISCRIMINATES and the obligation still would not discharge, because the
    # suite record did not carry the declared string either.
    led.discrimination, led.failed_before = verdicts, red
    assert led._reproduced_on_base() is not None


def test_it_still_engages_on_nothing_when_nothing_claims_to_pass(repo):
    """The control. Silence when there is no claim, not silence always."""
    led = ledger_for(repo)
    led.evidence[0].result = Result.FAIL
    assert stress.stress(led) == ({}, [])


# --- the base a claim-by-edit task is compared against ----------------------

def _hook(event, payload):
    import json
    import subprocess
    import sys
    from pathlib import Path

    return subprocess.run(
        [sys.executable, "-m", "core.hook", event],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=Path(__file__).resolve().parents[1],
    )


def test_a_task_opened_by_an_edit_still_has_a_base(repo):
    """The defect that cost 37% of a paid sweep.

    A prompt that states no claim opens a task anyway, and `Ledger.open_by_edit`
    attaches `feature_added` at the first edit. That ledger carried no base
    commit, so `stress` had no old tree to build and the discrimination check
    silently never ran - on six of sixteen runs, every one of them opened by an
    edit and no other.
    """
    from core.ledger import Ledger

    head = git(repo, "rev-parse", "HEAD")
    _hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "have a look at this"})
    assert Ledger.load(repo).base == head, "the task opened with nothing to compare against"

    target = repo / "src" / "app.py"
    _hook("PostToolUse", {"cwd": str(repo), "tool_name": "Edit",
                          "tool_input": {"file_path": str(target)}})
    back = Ledger.load(repo)
    assert back.claims, "the edit should have opened a claim"
    assert back.base == head, back.base


def test_the_base_does_not_move_once_the_task_has_opened(repo):
    """Adversarially: the base is HEAD at task open, not HEAD whenever asked.

    An agent that commits mid-task would otherwise move the very thing its work
    is being compared against, and the check would compare the change to itself.
    """
    from core.ledger import Ledger

    opened = git(repo, "rev-parse", "HEAD")
    _hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "have a look at this"})

    (repo / "src" / "app.py").write_text("# moved on\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", "mid-task")
    assert git(repo, "rev-parse", "HEAD") != opened

    _hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "have a look at this"})
    assert Ledger.load(repo).base == opened, "the base moved under the task"


# --- at what grain was the reproduction established? ------------------------

def test_a_suite_level_reproduction_says_so(repo):
    """Measured on B3: 7 of 7 reproductions came this way, 0 from a named test.

    The targeted path needs a PASSING record carrying a node id, and `pytest -q`
    prints passes as dots - the parsers hold 1,256 failing node records against
    four passing ones - so it is starved by construction. What is left is the
    suite path, which fires on the same single base-tree run that decides
    discrimination. Reporting both as plain green lines claims two findings
    where there is one.
    """
    from core.evidence import Evidence, Kind, Result, source_files, tree_hash
    from core.ledger import SUITE_GRAIN, Ledger
    from core.obligations import Claim
    from core.stress import DISCRIMINATES

    files = source_files(repo)
    suite = Evidence(kind=Kind.SUITE, identity="tests", result=Result.PASS,
                     observed=files, tree=tree_hash(repo, files), scope="source",
                     command="python -m pytest", passed=3, failed=0, counted=True)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], evidence=[suite],
                 base=stress.base_commit(repo),
                 discrimination={"tests": DISCRIMINATES}, failed_before=[])

    shown, grain = led._reproduction()
    assert shown is not None, "a suite red before and green now is still a reproduction"
    assert grain == SUITE_GRAIN, grain
    assert led._reproduced_on_base() is not None, "the old call must keep working"


def test_a_targeted_reproduction_carries_no_caveat(repo):
    """Adversarially: the caveat must not be pinned to every reproduction.

    A named test that was red on the base tree and passes now IS a second
    finding, and saying otherwise would understate it exactly as the suite case
    overstates it.
    """
    from core.evidence import Evidence, Kind, Result, source_files, tree_hash
    from core.ledger import Ledger
    from core.obligations import Claim

    files = source_files(repo)
    node = Evidence(kind=Kind.TEST, identity="tests/test_app.py::test_add",
                    result=Result.PASS, observed=files, tree=tree_hash(repo, files),
                    scope="source", command="python -m pytest", counted=True)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], evidence=[node],
                 base=stress.base_commit(repo), discrimination={},
                 failed_before=["tests/test_app.py::test_add"])

    shown, grain = led._reproduction()
    assert shown is not None, "red there, green here, by name"
    assert grain == "", grain


# --- the reproduction, asked rather than waited for -------------------------

def test_a_red_test_confirmed_green_is_a_named_reproduction(repo):
    """The other half of 5.13, and the end of the one-fact-twice problem.

    `stress` already learns which tests were red on the base tree. Running those
    same node ids against the tree as it is now establishes red-then-green BY
    NAME, instead of resting on the same base-tree run that decided
    discrimination - which supplied 0 of 7 reproductions on the B3 sweep.
    """
    from core.ledger import Ledger
    from core.obligations import Claim
    from core.stress import CONFIRMED, confirm

    save_config(repo, Config(profile="guide", commands={"tests": NODES}))
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], base=stress.base_commit(repo),
                 failed_before=["tests/test_app.py::test_add"],
                 touched=["tests/test_app.py"])
    found = confirm(led)

    assert [e.identity for e in found] == ["tests/test_app.py::test_add"], found
    led.add(found)
    shown, grain = led._reproduction()
    assert shown is not None
    assert grain == "", "a named red-then-green test is not a suite-level finding"

    # Asked once per task: the base does not move, so neither can the answer.
    assert any(d["what"] == CONFIRMED for d in led.decisions)
    assert confirm(led) == []


def test_a_test_still_red_is_not_a_reproduction(repo):
    """Adversarially: confirming must report what it finds, not what it hoped.

    A test red on the base tree and STILL red now is the ordinary shape of
    unfinished work, and returning it would manufacture a reproduction out of a
    failure.
    """
    from core.ledger import Ledger
    from core.obligations import Claim
    from core.stress import confirm

    save_config(repo, Config(profile="guide", commands={"tests": NODES}))
    (repo / "tests" / "test_app.py").write_text(
        "def test_add():\n    assert False\n", encoding="utf-8")
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], base=stress.base_commit(repo),
                 failed_before=["tests/test_app.py::test_add"],
                 touched=["tests/test_app.py"])

    assert confirm(led) == []


def test_a_command_naming_a_path_is_narrowed_not_widened(repo):
    """`pytest tests -q` is what the whole corpus declares.

    Appending ids to it would run the directory *and* the ids - the suite again
    at a higher price - so the path is substituted out instead. An append-only
    version declined on all sixteen corpus tasks, which is a mechanism that is
    correct and never fires.
    """
    from core.stress import _targeted

    run = _targeted(f'"{sys.executable}" -m pytest tests -q', repo,
                    ("tests/test_app.py::test_add",))
    assert run.endswith("-q tests/test_app.py::test_add"), run
    assert " tests " not in run, run


def test_a_command_it_cannot_read_is_declined(repo):
    """Adversarially, twice over.

    `no:cacheprovider` is a flag's value, not a path: no slash, no extension,
    indistinguishable from `tests` by shape alone. Existence is what separates
    them, and a token that is neither a flag nor a real path means the command
    is not understood - which is declined, never guessed at.

    And an id outside the declared path would make the run *wider* than what the
    project sanctioned, which is the one thing substitution must never do.
    """
    from core.stress import _targeted

    assert _targeted("python -m pytest -p no:cacheprovider", repo,
                     ("tests/test_app.py::test_add",)) == ""
    assert _targeted("make test", repo, ("tests/test_app.py::test_add",)) == ""
    assert _targeted("python -m pytest src -q", repo,
                     ("tests/test_app.py::test_add",)) == ""


def test_an_edit_after_the_tests_does_not_lose_the_whole_check(repo):
    """Requiring a FRESH pass cost two of sixteen paid runs their answer.

    The question is about the base tree and the declared command, and neither
    moves when the agent edits a file after running the tests. But that edit
    stales every passing record, so the gate closed and the run recorded no
    verdict, no failed_before, and therefore no reproduction either.

    Forward - a stale pass is still a claim that the tests passed, so it is
    still questioned. Adversarially - a record whose files are GONE claims
    nothing coherent, and nothing that never passed is questioned at all.
    """
    from core.evidence import Freshness
    from core.stress import _passing

    led = ledger_for(repo)
    assert _passing(led), "a fresh pass must be questioned"

    # The ordinary shape: tests run green, then one more edit lands.
    (repo / "src" / "app.py").write_text(
        "def add(a, b):\n    return a + b  # one more touch\n", encoding="utf-8")
    assert led.evidence[0].freshness(repo) is Freshness.STALE
    assert _passing(led), "an edit after the tests must not lose the check"

    # Gone is different: the files the record observed no longer exist.
    (repo / "src" / "app.py").unlink()
    (repo / "tests" / "test_app.py").unlink()
    assert led.evidence[0].freshness(repo) is Freshness.GONE
    assert not _passing(led), "a record whose files vanished claims nothing"


def test_nothing_claiming_to_pass_is_still_not_questioned(repo):
    """The guard the change must not remove: no pass, nothing to question."""
    from core.evidence import Evidence, Kind, Result, source_files, tree_hash
    from core.ledger import Ledger
    from core.obligations import Claim
    from core.stress import _passing

    observed = source_files(repo)
    failing = Evidence(kind=Kind.SUITE, identity="python pytest", result=Result.FAIL,
                       observed=observed, tree=tree_hash(repo, observed), scope="source",
                       command=SUITE, passed=0, failed=1, counted=True)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], evidence=[failing])
    assert not _passing(led)


def test_the_ledger_records_which_commands_were_declared(repo):
    """A bundle that cannot say which gate closed cannot explain its result.

    `stress` declines when a project declares no command. On the B3 sweep that
    gate could not be told apart from the others after the fact, because the
    config lived only on disk in a workspace that no longer existed.

    Forward - the declared commands are in the saved ledger. Adversarially -
    loading never takes them from that snapshot, because the config on disk is
    the truth about a repository now and yesterday's copy must not override it.
    """
    import json

    led = ledger_for(repo)
    led.save()
    written = json.loads(led.path.read_text(encoding="utf-8"))
    assert written["config"]["commands"] == {"tests": SUITE}
    assert written["config"]["profile"] == "guide"

    save_config(repo, Config(profile="strict", commands={"tests": "make check"}))
    back = Ledger.load(repo)
    assert back.config.commands == {"tests": "make check"}, "disk must win"
    assert back.config.profile == "strict"


# --- the gate must see work done through the shell --------------------------

def test_a_patch_written_through_the_shell_still_opens_the_gate(repo):
    """The 12.5% bypass measured on B4.

    `jinja2-0cd69481` shipped a 5,396-line patch touching src/jinja2/utils.py,
    graded RESOLVED, with ledger.touched empty and seen empty - the agent wrote
    through `printf` and redirection, so no Read/Edit/Write event ever reached
    the runtime. No claim opened, and on_stop returned on its first line.

    Enumerating shell write syntax is a race nobody wins. The working tree
    already knows.
    """
    from core.ledger import Ledger

    _hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "have a look at this"})
    assert Ledger.load(repo).claims == [], "the prompt states no claim, by design"

    # Written the way the agent actually wrote it: no tool event, just a shell
    # redirect landing in the working tree.
    (repo / "src" / "app.py").write_text(
        "def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n",
        encoding="utf-8")

    _hook("Stop", {"cwd": str(repo), "last_assistant_message": "done"})
    back = Ledger.load(repo)
    assert back.claims, "source changed and the gate saw nothing"
    assert "src/app.py" in back.touched, back.touched


def test_a_working_tree_of_only_prose_still_opens_nothing(repo):
    """Adversarially: the fix must not make every session a gated task.

    A changelog or a README is not a claim about behaviour, and `attrs-5d6d21aa`
    is the case that matters - its ONLY observed edit was a changelog, which is
    why no claim opened there either. Prose keeps not opening one; what changed
    is that source no longer goes unseen.
    """
    from core.ledger import Ledger

    _hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "have a look at this"})
    (repo / "CHANGES.md").write_text("- a note about the release\n", encoding="utf-8")

    _hook("Stop", {"cwd": str(repo), "last_assistant_message": "done"})
    assert Ledger.load(repo).claims == [], "prose must not open a claim"


def test_a_session_that_was_never_given_a_task_stays_silent(repo):
    """Adversarially: no request, no gate, whatever the tree looks like.

    Without this the fix would gate a user who merely has uncommitted work
    sitting in their repository when a session starts.
    """
    from core.ledger import Ledger

    (repo / "src" / "app.py").write_text("def add(a, b):\n    return a * b\n", encoding="utf-8")
    _hook("Stop", {"cwd": str(repo), "last_assistant_message": "done"})
    assert Ledger.load(repo).claims == []
