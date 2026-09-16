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
