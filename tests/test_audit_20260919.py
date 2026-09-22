"""Defects an external audit reproduced on 2026-09-18's tree, closed.

`docs/research/audit_2026_09_19/`. Every probe there reproduced byte-for-byte
when re-run here, so these are not hypotheses; each test below is the audit's
counterexample turned into a standing guard, with the forward case beside it so
the guard cannot pass by refusing everything.

The theme of the worst of them is one sentence: **selection is not execution,
recognition is not execution, and two true observations of different things are
not one observation.**
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from core import parsers, stress
from core.config import Config
from core.evidence import Evidence, Kind, Result, source_files, tree_hash
from core.ledger import Ledger

from core.stress import DISCRIMINATES


def git(root, *args):
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, f"git {' '.join(args)}: {done.stderr}"
    return done.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "probe@example.invalid")
    git(tmp_path, "config", "user.name", "probe")
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(
        "def test_a():\n    assert True\n", encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def ledger_for(repo, command, red):
    return Ledger(root=repo, task="t", base=git(repo, "rev-parse", "HEAD"),
                  failed_before=list(red), _config=Config(commands={"tests": command}))


# --- F1: a test that did not run, or did not pass, is not a reproduction -----

def test_fail_fast_does_not_credit_a_test_that_never_ran(repo):
    """The audit's first counterexample.

    Under `-x` the first selected test fails and the later ones never execute.
    They were credited as passing reproductions, because the old code subtracted
    the named failures and called the remainder green. `executed-b` is written
    by the test itself, so its absence is proof the test never ran.
    """
    (repo / "tests" / "test_a.py").write_text(
        "def test_a():\n    assert False\n", encoding="utf-8")
    (repo / "tests" / "test_b.py").write_text(
        "from pathlib import Path\n"
        "def test_b():\n    Path('executed-b').write_text('yes')\n    assert True\n",
        encoding="utf-8")
    led = ledger_for(repo, f"{sys.executable} -m pytest -q -x tests",
                     ["tests/test_a.py::test_a", "tests/test_b.py::test_b"])
    records = stress.confirm(led)
    named = {r.identity for r in records if r.result is Result.PASS}
    assert "tests/test_a.py::test_a" not in named, "a failing test was called a pass"
    if not (repo / "executed-b").exists():
        assert "tests/test_b.py::test_b" not in named, (
            "credited a test whose own side effect proves it never ran")


def test_a_skipped_test_is_not_a_reproduction(repo):
    """The audit's second, and it needs no fail-fast at all.

    pytest reports the one requested node as skipped; the old code emitted PASS
    and the ledger accepted it as the named reproduction.
    """
    (repo / "tests" / "test_a.py").write_text(
        "import pytest\n\n\n@pytest.mark.skip(reason='probe')\n"
        "def test_a():\n    assert False\n", encoding="utf-8")
    led = ledger_for(repo, f"{sys.executable} -m pytest -q tests",
                     ["tests/test_a.py::test_a"])
    records = stress.confirm(led)
    assert [r.identity for r in records if r.result is Result.PASS] == []
    led.add(records)
    assert led._reproduction()[0] is None


def test_a_test_that_really_passes_is_still_credited(repo):
    """Forward. Without this, the two tests above pass by crediting nothing."""
    (repo / "tests" / "test_a.py").write_text(
        "def test_a():\n    assert True\n", encoding="utf-8")
    led = ledger_for(repo, f"{sys.executable} -m pytest -q tests",
                     ["tests/test_a.py::test_a"])
    records = stress.confirm(led)
    green = [r.identity for r in records if r.result is Result.PASS]
    assert green == ["tests/test_a.py::test_a"], records


def test_the_confirmation_run_asks_for_explicit_outcomes(repo):
    """`-rA` is what makes the above readable rather than inferred."""
    run = stress._targeted(f"{sys.executable} -m pytest -q -x tests", repo,
                           ("tests/test_a.py::test_a",))
    assert "-rA" in run.split()
    assert "-x" not in run.split(), "fail-fast hides the outcome being asked for"


def test_maxfail_with_a_separate_value_does_not_break_the_command(repo):
    """`--maxfail 3` spends a second token; dropping only the flag left `3`
    looking like a path, which silently disabled confirmation entirely."""
    run = stress._targeted(f"{sys.executable} -m pytest --maxfail 3 tests", repo,
                           ("tests/test_a.py::test_a",))
    assert run, "confirmation went silent instead of running"
    assert "3" not in run.split()


# --- F5: reading a report is not running the tests ---------------------------

def test_reading_a_tap_file_is_not_a_test_run(tmp_path):
    """`cat fixture.tap` produced a counted passing suite with ran_tests true."""
    out = "TAP version 13\nok 1 - sample\n1..1\n"
    assert parsers.parse("cat fixture.tap", out, 0, tmp_path) == []
    assert parsers.parse("type fixture.tap", out, 0, tmp_path) == []


@pytest.mark.parametrize("command", [
    "node --test",
    "npm test",
    "turbo test",
    "deno test",
    # Named harnesses, which `claims_to_run_tests` does not match at all - they
    # rely entirely on the runner allow-list.
    "prove -r t/",
    "bats tests/",
    # ...and the same harnesses one word later. `npx prove` is how a project
    # without a global install runs it, and stripping the launcher is done
    # inside `runs_tap` rather than in `_bare`, which decides dispatch for every
    # command in the file.
    "npx prove t/",
    "pnpm exec bats tests/",
])
def test_a_real_tap_runner_is_still_read(command, tmp_path):
    """Forward, eight ways. The fix must not silence the runners it was for."""
    out = "TAP version 13\nok 1 - sample\n1..1\n"
    records = parsers.parse(command, out, 0, tmp_path)
    assert records and records[0].result is Result.PASS, command
    assert records[0].ran_tests, command


# --- F4: two facts about different checks are not one reproduction -----------

def _passing_suite(root):
    observed = source_files(root)
    return Evidence(Kind.SUITE, "pytest tests", Result.PASS, observed,
                    tree_hash(root, observed), passed=1, counted=True, scope="source")


def test_a_discriminating_typecheck_does_not_reproduce_a_test_suite(repo):
    """The audit joined a discriminating typecheck to a passing test suite and
    the ledger reported red-then-green. Different checks, one claim."""
    led = Ledger(root=repo, task="t", base=git(repo, "rev-parse", "HEAD"),
                 evidence=[_passing_suite(repo)],
                 discrimination={"typecheck": DISCRIMINATES})
    assert led._reproduction()[0] is None


def test_a_discriminating_test_suite_still_reproduces(repo):
    """Forward: the same shape with the kinds matching is the real case."""
    led = Ledger(root=repo, task="t", base=git(repo, "rev-parse", "HEAD"),
                 evidence=[_passing_suite(repo)],
                 discrimination={"tests": DISCRIMINATES})
    shown, grain = led._reproduction()
    assert shown is not None and "suite-level" in grain


# --- F11: one redacted copy and one unredacted copy is not a redaction -------

def test_a_credential_does_not_survive_in_evidence_detail(repo):
    """The output sample was scrubbed and `Evidence.detail` kept the same bytes."""
    fake = "ghp_" + "PROBEONLY0000000000000000000000"
    records = parsers.parse("python -m pytest tests -q",
                            f"1 passed in 0.01s\n{fake}\n", 0, repo)
    assert records
    serialized = json.dumps([r.to_dict() for r in records])
    assert fake not in serialized
    assert "REDACTED" in serialized


def test_ordinary_detail_is_untouched(repo):
    """Forward: redaction that ate normal output would break the report."""
    records = parsers.parse("python -m pytest tests -q",
                            "1 passed in 0.01s\n", 0, repo)
    assert records and "1 passed" in records[0].detail


# --- F7: absence of a failure is not a pass ---------------------------------

def test_a_test_missing_from_the_failures_is_not_called_vacuous(repo):
    """The audit's inference bug.

    A test absent from `failed_before` was reported as having passed on the base
    tree. It can be absent because it was skipped, deselected, never reached
    under fail-fast, or because the run died first. None of those is a pass, and
    accusing correct work is the one error these checks must not make.
    """
    led = Ledger(root=repo, task="t", base=git(repo, "rev-parse", "HEAD"),
                 touched=["tests/test_b.py"],
                 discrimination={"tests": DISCRIMINATES},
                 failed_before=["tests/test_a.py::test_a"])
    from core import assumptions
    assert assumptions.vacuous_tests(led) == []


def test_a_test_observed_passing_on_the_base_tree_is_still_named(repo):
    """Forward: with the positive observation, the finding still fires."""
    led = Ledger(root=repo, task="t", base=git(repo, "rev-parse", "HEAD"),
                 touched=["tests/test_b.py"],
                 discrimination={"tests": DISCRIMINATES},
                 failed_before=["tests/test_a.py::test_a"],
                 passed_before=["tests/test_b.py::test_b"])
    from core import assumptions
    assert assumptions.vacuous_tests(led) == ["tests/test_b.py"]


def test_the_base_tree_run_asks_pytest_to_name_its_passes(repo):
    """`passed_before` cannot exist unless the run was asked for outcomes."""
    assert stress._with_outcomes("python -m pytest tests -q").endswith("-rA")
    assert stress._with_outcomes("python -m pytest -rA tests").count("-rA") == 1
    assert stress._with_outcomes("npm test") == "npm test", "left alone when not pytest"


# --- F7: what a command printed is kept even when it is not evidence --------

def test_producer_output_is_captured_even_when_nothing_parses(repo, monkeypatch):
    """Running a producer to look at its shape is the habit the check rewards.

    Output was only kept when the parsers recognised a test runner, so
    `node -e "console.log(...)"` - the textbook case - was dropped entirely and
    the assumption check could never confirm a pattern against it.
    """
    from core import hook
    from core.ledger import STATE_DIR

    led = Ledger(root=repo, task="t", base=git(repo, "rev-parse", "HEAD"))
    (repo / STATE_DIR).mkdir(exist_ok=True)
    led.save()

    seen = {}
    monkeypatch.setattr(Ledger, "load", classmethod(lambda cls, root: led))
    monkeypatch.setattr(Ledger, "save", lambda self: seen.setdefault("saved", True))
    hook.on_post_tool({"tool_name": "Bash",
                       "tool_input": {"command": 'node -e "console.log(1)"'},
                       "tool_response": {"stdout": "TAP-ish sample line\n", "stderr": ""}},
                      repo)
    assert len(led.outputs) == 1, led.outputs
    assert "sample line" in led.outputs[0]["text"]


def test_no_open_task_means_no_state_is_created(repo, monkeypatch):
    """Adversarial: capture must not invent a ledger for an untracked command."""
    from core import hook
    from core.ledger import STATE_DIR

    hook.on_post_tool({"tool_name": "Bash",
                       "tool_input": {"command": "echo hello"},
                       "tool_response": {"stdout": "hello\n", "stderr": ""}}, repo)
    assert not (repo / STATE_DIR / "ledger.json").exists()
