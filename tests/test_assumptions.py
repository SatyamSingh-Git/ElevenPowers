"""Claims about things nobody ran.

Design: `docs/design/unverified-assumptions.md`. The check exists because one
day in this repository produced seven defects of a single shape - a pattern
written to describe some producer's output, and the producer never run. Every
one was found by executing the real thing; none by thinking harder.

The forward case is the one that must stay silent, because a check that fires on
every pattern is indistinguishable from the feature being absent, and a check
that fires on none is the state that let those seven through.
"""

from __future__ import annotations

import subprocess

import pytest

from core import assumptions
from core.ledger import Ledger
from core.obligations import Claim


def git(root, *args):
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, f"git {' '.join(args)}: {done.stderr}"
    return done.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "probe@example.invalid")
    git(tmp_path, "config", "user.name", "probe")
    (tmp_path / "parser.py").write_text("PATTERNS = {}\n", encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def add_pattern(repo, body):
    (repo / "parser.py").write_text(f'import re\nCOUNT = re.compile(r"{body}")\n',
                                    encoding="utf-8")


def ledger_with(repo, output=""):
    led = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                 base=git(repo, "rev-parse", "HEAD"), touched=["parser.py"])
    if output:
        led.saw_output("node --test", output)
    return led


# --- the real case, rebuilt ------------------------------------------------

# Exactly the shape that shipped unverified: a TAP counter pattern, written
# from memory of what `node --test` prints.
TAP_PATTERN = r"^\s*#\s*(pass|fail)\s+\d+\s*$"
REAL_TAP = "1..3\n# tests 3\n# pass 2\n# fail 1\n"


def test_a_pattern_the_task_actually_saw_is_silent(repo):
    """Forward. The command was run, the output matched, nothing to say.

    Without this the check could be firing on every pattern ever written, which
    is the same as not having it.
    """
    add_pattern(repo, TAP_PATTERN)
    led = ledger_with(repo, REAL_TAP)
    assert assumptions.unverified(led) == []


def test_a_pattern_nothing_produced_is_named(repo):
    """The day's defect, caught before the agent says done.

    The pattern is written from memory; the command that would confirm it was
    never run. The ledger knows, and until now nobody asked it.
    """
    add_pattern(repo, TAP_PATTERN)
    led = ledger_with(repo, "Ran 3 checks, all good.\n")     # something else entirely
    found = assumptions.unverified(led)
    assert found == [TAP_PATTERN], found
    assert "run the thing and look" in " ".join(assumptions.wording(found, []))


def test_a_pattern_written_before_the_command_ran_is_still_verified(repo):
    """Order must not matter: looking first is the behaviour to encourage.

    The output is kept, so a pattern written after the command - or before it -
    is confirmed the same way. Checking only as output flowed past would have
    punished exactly the habit this is meant to reward.
    """
    led = ledger_with(repo, REAL_TAP)
    add_pattern(repo, TAP_PATTERN)                            # written afterwards
    assert assumptions.unverified(led) == []


# --- adversarial ------------------------------------------------------------

def test_running_nothing_at_all_is_not_an_accusation(repo):
    """Silence, not a complaint, when there is no evidence either way.

    A task that ran no commands cannot have confirmed anything, and saying "none
    of your patterns are verified" there is an accusation dressed as a finding.
    """
    add_pattern(repo, TAP_PATTERN)
    assert assumptions.unverified(ledger_with(repo)) == []


def test_a_pattern_matching_the_empty_string_is_never_reported(repo):
    """This module shipped one of these, so it is not hypothetical.

    `(?:x)?` matches every output ever captured, so it is confirmed by anything
    and cannot be reported. A guard skipping such patterns early was written
    here, and flipping it proved it did nothing - the assertion below holds with
    or without it - so the guard went rather than stay looking load-bearing.
    """
    add_pattern(repo, r"(?:(?:[^\s:]+:){1,2}[ \t]*)?")
    assert assumptions.unverified(ledger_with(repo, "anything at all\n")) == []


def test_ordinary_strings_are_not_patterns(repo):
    """A message is not a claim about text, and must not be treated as one."""
    (repo / "parser.py").write_text(
        'MESSAGE = "could not read the configuration file"\n'
        'NAME = "typescript"\n', encoding="utf-8")
    assert assumptions.unverified(ledger_with(repo, "unrelated output\n")) == []


def test_a_comment_is_not_a_claim(repo):
    """Adversarially: sample output pasted into a docstring is documentation."""
    (repo / "parser.py").write_text(
        '# the runner prints "^\\s*#\\s*(pass|fail)\\s+\\d+$" at the end\n'
        "VALUE = 1\n", encoding="utf-8")
    assert assumptions.unverified(ledger_with(repo, "unrelated output\n")) == []


def test_an_unparseable_pattern_is_skipped_rather_than_guessed(repo):
    """Half-written code is not a finding."""
    (repo / "parser.py").write_text('BROKEN = "^(unclosed[\\d+"\n', encoding="utf-8")
    assert assumptions.unverified(ledger_with(repo, "unrelated\n")) == []


# --- the vacuous probe, computed -------------------------------------------

def test_a_new_test_that_passes_on_the_base_tree_is_named(repo):
    """Four of these shipped in one day, caught only by flipping them by hand.

    `core/stress.py` already knows which tests were red on the base commit. A
    test the task added which is not among them ran green against code that did
    not contain the change.
    """
    led = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                 base=git(repo, "rev-parse", "HEAD"),
                 touched=["tests/test_new.py", "parser.py"],
                 discrimination={"tests": "yes"},
                 failed_before=["tests/test_other.py::test_thing"])
    assert assumptions.vacuous_tests(led) == ["tests/test_new.py"]
    assert "did not test this change" in " ".join(
        assumptions.wording([], ["tests/test_new.py"]))


def test_a_new_test_that_failed_on_the_base_tree_is_silent(repo):
    """Forward: red there, green here, which is the reproduction it should be."""
    led = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                 base=git(repo, "rev-parse", "HEAD"),
                 touched=["tests/test_new.py"],
                 discrimination={"tests": "yes"},
                 failed_before=["tests/test_new.py::test_it"])
    assert assumptions.vacuous_tests(led) == []


def test_without_a_base_tree_run_nothing_is_claimed(repo):
    """Adversarially: no run, no accusation.

    The base tree may not have been asked at all - no declared command, no base
    commit, a runner that could not start. Reporting every new test as vacuous
    there would be the loudest possible way to say nothing.
    """
    led = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                 touched=["tests/test_new.py"])
    assert assumptions.vacuous_tests(led) == []

    asked = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                   base=git(repo, "rev-parse", "HEAD"),
                   touched=["tests/test_new.py"],
                   discrimination={"tests": "yes"}, failed_before=[])
    assert assumptions.vacuous_tests(asked) == [], (
        "nothing red on base is already reported as a discrimination verdict")

    # And the state the gate itself exists for, which neither case above
    # reaches: a ledger carrying red tests left from some earlier run, with no
    # base and no verdict of its own. Flipping the gate showed both cases above
    # passed without it; this is the one that makes it load-bearing.
    stale = Ledger(root=repo, task="t", claims=[Claim.BUG_FIXED],
                   touched=["tests/test_new.py"],
                   failed_before=["tests/test_other.py::test_thing"])
    assert assumptions.vacuous_tests(stale) == [], (
        "accused a test without having asked the base tree in this task")
