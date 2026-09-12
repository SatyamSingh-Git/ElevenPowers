"""The sixteen defects an external audit reproduced, as tests.

Each test asserts the behaviour the system is supposed to have. One still
carrying `xfail(strict=True)` is a defect that is still there; the marker keeps
the suite green so ordinary work is not drowned in noise, and the moment the
defect is fixed the test turns from xfail to xpass and **fails the run**, which
forces the marker off. The ones without a marker are fixed, and will fail if
that stops being true.

A defect that lives in a document is a note. A defect that lives here cannot be
quietly un-fixed. The count of remaining `xfail`s is how many are left.

Source: `docs/research/audit_2026_09_11/`. Identifiers match PLAN.md section 4.
"""

from __future__ import annotations

import contextlib
import io
import json
import math
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from core import hook, parsers
from core.config import Config
from core.evidence import (
    Evidence, Freshness, Kind, Result, source_files, tree_hash, vcs_state,
)
from core.ledger import Ledger, Status
from core.obligations import Claim
from core.repeat import runs_needed
from core.verify import dischargeable
from eval.live import verify

defect = lambda ident, why: pytest.mark.xfail(strict=True, reason=f"{ident}: {why}")  # noqa: E731


@pytest.fixture
def project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src/app.py").write_text("value = 0\n", encoding="utf-8")
    (tmp_path / "tests/test_app.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def committed(project):
    for args in (["init", "-q"], ["add", "."],
                 ["-c", "user.name=A", "-c", "user.email=a@example.invalid",
                  "commit", "-qm", "baseline"]):
        subprocess.run(["git", *args], cwd=project, check=True, capture_output=True)
    return project


def suite_record(root: Path, outcome: Result, when: float, identity: str = "pytest") -> Evidence:
    paths = source_files(root)
    return Evidence(Kind.SUITE, identity, outcome, paths, tree_hash(root, paths),
                    command="pytest -q", passed=2,
                    failed=int(outcome is Result.FAIL), at=when)


# --- R1, R2, R3: what invalidates evidence -----------------------------------

def test_changing_an_already_dirty_file_stales_its_evidence(committed):
    """The whole promise is that editing a file invalidates what depended on it.

    An earlier version of this pinned `vcs_state` to a constant, to force the
    branch where git resolves. That made the test demand the tie-breaker be
    removed rather than corrected, and it stubbed out the exact function the fix
    changed — so the fix landed and the test could not see it. Real git, no
    mocks: two edits of an already-modified file now differ, and where git does
    not resolve the answer is `STALE` anyway, so this is the same either way.
    """
    app = committed / "src/app.py"
    app.write_text("value = 1\n", encoding="utf-8")
    evidence = parsers.parse("pytest -q", "1 passed in 0.1s", 0, committed)[-1]
    app.write_text("value = 999\n", encoding="utf-8")
    assert evidence.freshness(committed) is Freshness.STALE


def test_two_edits_of_a_dirty_file_are_told_apart(committed):
    """What R1 was underneath: a porcelain status names files, not contents."""
    app = committed / "src/app.py"
    app.write_text("value = 1\n", encoding="utf-8")
    first = vcs_state(committed)
    app.write_text("value = 999\n", encoding="utf-8")
    assert first and vcs_state(committed) != first


def test_adding_a_test_file_stales_a_suite_result(project):
    """Built through the parser, because the record has to carry its own scope.

    Constructed by hand it proves nothing about what a real suite run records,
    and a hand-built record is what let this pass while the production path
    still stored a list that could never grow.
    """
    evidence = parsers.parse("pytest -q", "1 passed in 0.1s", 0, project)[-1]
    (project / "tests/test_new.py").write_text("def test_no():\n    assert False\n", encoding="utf-8")
    assert evidence.freshness(project) is Freshness.STALE


@defect("R3", "the ledger rejects STALE and says nothing about GONE")
def test_deleting_an_observed_file_is_not_verified(project):
    ledger = Ledger(project, claims=[Claim.REFACTOR_SAFE],
                    evidence=[suite_record(project, Result.PASS, 1)])
    (project / "src/app.py").unlink()
    assert ledger.evidence[0].freshness(project) is Freshness.GONE
    assert ledger.status() is not Status.VERIFIED


# --- R4: which record speaks for an identity ---------------------------------

@defect("R4", "an older pass satisfies while the newest failure is excused as pre-existing")
def test_a_failure_after_a_pass_is_not_verified(project):
    ledger = Ledger(project, claims=[Claim.REFACTOR_SAFE], evidence=[
        suite_record(project, Result.FAIL, 1),
        suite_record(project, Result.PASS, 2),
        suite_record(project, Result.FAIL, 3),
    ])
    assert ledger.evidence[-1].result is Result.FAIL
    assert ledger.status() is not Status.VERIFIED


@defect("R4", "no-new-failures compares counts, not which tests failed")
def test_the_same_number_of_different_failures_is_not_tolerated(project):
    first, last = suite_record(project, Result.FAIL, 1), suite_record(project, Result.FAIL, 2)
    first.detail = "FAILED tests/test_old.py::test_old"
    last.detail = "FAILED tests/test_new.py::test_new"
    ledger = Ledger(project, claims=[Claim.REFACTOR_SAFE], evidence=[first, last])
    assert ledger.status() is not Status.VERIFIED


# --- R5: what counts as having run the suite ---------------------------------

@pytest.mark.parametrize("command,output", [
    ("echo pytest", "pytest\n"),
    ("python -m pytest --version", "pytest 9.1.1\n"),
])
@defect("R5", "a substring match plus a zero exit code is treated as a suite run")
def test_a_command_that_ran_no_tests_is_not_a_passing_suite(project, command, output):
    evidence = parsers.parse(command, output, 0, project)
    ledger = Ledger(project, claims=[Claim.REFACTOR_SAFE], evidence=evidence)
    assert ledger.status() is not Status.VERIFIED


# --- R6: reading is not writing ----------------------------------------------

@defect("R6", "_test_written_and_suite_green searches touched union seen, and seen includes reads")
def test_reading_an_existing_test_is_not_writing_one(project):
    with patch.object(parsers, "vcs_state", return_value=""):
        evidence = parsers.parse("pytest -q", "1 passed in 0.1s", 0, project)
    ledger = Ledger(project, claims=[Claim.BUG_FIXED],
                    seen=["tests/test_app.py"], evidence=evidence)
    assert ledger.status() is not Status.VERIFIED


# --- R7, R8: task identity and risk ------------------------------------------

@defect("R7", "on_prompt reuses the task id and carries the previous task's state forward")
def test_a_new_request_starts_a_clean_task(project):
    before = Ledger(project, task="previous", request="Fix the previous bug",
                    claims=[Claim.BUG_FIXED], seen=["tests/test_app.py"],
                    evidence=[suite_record(project, Result.PASS, 1)], guided=True)
    before.save()
    with contextlib.redirect_stdout(io.StringIO()):
        hook.on_prompt({"prompt": "Implement a new parser"}, project)
    after = Ledger.load(project)
    assert after.task != "previous"
    assert after.evidence == []
    assert after.seen == []
    assert after.guided is False


@defect("R7", "two readers, two writers: the first writer's decision is lost")
def test_concurrent_writers_do_not_lose_decisions(project):
    Ledger(project, claims=[Claim.BUG_FIXED]).save()
    a, b = Ledger.load(project), Ledger.load(project)
    a.note("event-A", "first worker")
    b.note("event-B", "second worker")
    a.save()
    b.save()
    kept = {d["what"] for d in Ledger.load(project).decisions}
    assert kept == {"event-A", "event-B"}


@defect("R8", "observe_edit returns before updating touched and risk when a claim exists")
def test_a_later_sensitive_edit_raises_risk(project):
    ledger = Ledger(project, request="Fix the bug", claims=[Claim.BUG_FIXED])
    ledger.observe_edit("src/auth/session.py")
    assert "src/auth/session.py" in ledger.touched
    assert ledger.risk.value != "low"


# --- R9: what repetition certifies -------------------------------------------

@defect("R9", "any STABILITY record satisfies, whatever command it repeated")
def test_repeating_an_unrelated_command_does_not_certify_stability(project):
    flaky = suite_record(project, Result.FAIL, 1)
    flaky.kind, flaky.identity, flaky.runs, flaky.failed = Kind.STABILITY, "pytest test_worker.py", 10, 1
    unrelated = suite_record(project, Result.PASS, 2)
    unrelated.kind, unrelated.identity, unrelated.runs, unrelated.failed = Kind.STABILITY, "python -c pass", 300, 0
    ledger = Ledger(project, claims=[Claim.BUG_FIXED],
                    request="Fix the flaky test failure", evidence=[flaky, unrelated])
    stability = next(c for c in ledger.verdicts()[0].checks if c.obligation.key == "stable")
    assert not (stability.met and stability.evidence.identity == "python -c pass")


@defect("R9", "the cap returns 300 where the arithmetic needs 2995, and the report does not say so")
def test_the_run_cap_does_not_overstate_confidence(project):
    rate = 0.001
    needed = runs_needed(rate)
    exact = math.ceil(math.log(0.05) / math.log(1 - rate))
    assert needed >= exact or (1 - rate) ** needed <= 0.05


@defect("R3/R1", "stale evidence is not offered to self-discharge, so it is never refreshed")
def test_stale_evidence_is_schedulable_for_re_running(project):
    evidence = suite_record(project, Result.PASS, 1)
    (project / "src/app.py").write_text("value = 98765\n", encoding="utf-8")
    ledger = Ledger(project, claims=[Claim.REFACTOR_SAFE], evidence=[evidence],
                    _config=Config(commands={"tests": "pytest -q"}))
    assert ledger.status() is Status.STALE
    assert dischargeable(ledger) == ["tests"]


# --- E1: the grader ----------------------------------------------------------

BUGGY = "def double(n):\n    return n\n\n\ndef label():\n    return 'ok'\n"
FIXED = "def double(n):\n    return n * 2\n\n\ndef label():\n    return 'ok'\n"
KEEP = "from src.app import label\n\n\ndef test_label():\n    assert label() == 'ok'\n"
NEW = "from src.app import double\n\n\ndef test_double():\n    assert double(2) == 4\n"


@pytest.fixture
def upstream(tmp_path):
    """A repository with a bug at one commit and its maintainer's fix at the next.

    Real subprocesses rather than a mocked `subprocess.run`. The audit's own
    probe established what the grader invoked, and what it invokes is not the
    claim: the claim is what it then says about a patch.
    """
    from eval.live import materialise
    from eval.task import Task

    repo = tmp_path / "upstream"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()
    for rel, body in (("conftest.py", ""), ("src/__init__.py", ""),
                      ("src/app.py", BUGGY), ("tests/test_keep.py", KEEP)):
        (repo / rel).write_text(body, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True, capture_output=True)
    base = _commit(repo, "the code before the fix")

    (repo / "src/app.py").write_text(FIXED, encoding="utf-8")
    (repo / "tests/test_new.py").write_text(NEW, encoding="utf-8")
    _commit(repo, "double() returned its argument unchanged")

    task = Task(name="graded", prompt="double is wrong", files={}, hidden="", why="E1",
                source={"repo": str(repo), "base": base, "env": {},
                        "hidden_files": {"tests/test_new.py": NEW},
                        "f2p": ["tests/test_new.py::test_double"],
                        "p2p": ["tests/test_keep.py::test_label"]})
    root = tmp_path / "work"
    materialise(task, root)
    return task, root


def _commit(repo: Path, message: str) -> str:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=A",
                    "-c", "user.email=a@example.invalid", "commit", "-qm", message],
                   check=True, capture_output=True)
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()


def test_a_correct_patch_grades_as_resolved(upstream):
    """The control. A preservation check that rejects everything proves nothing."""
    task, root = upstream
    (root / "src/app.py").write_text(FIXED, encoding="utf-8")
    assert verify(task, root).resolved


def test_a_patch_that_breaks_an_existing_test_is_not_resolved(upstream):
    """E1: this returned True, on the measurement built to catch exactly it."""
    task, root = upstream
    (root / "src/app.py").write_text(FIXED.replace("'ok'", "'broken'"), encoding="utf-8")
    graded = verify(task, root)
    assert not graded.resolved
    assert graded.outcome == "regressed"


def test_editing_the_preserved_test_does_not_rescue_the_patch(upstream):
    """Otherwise the preservation set asks the agent to mark its own work twice."""
    task, root = upstream
    (root / "src/app.py").write_text(FIXED.replace("'ok'", "'broken'"), encoding="utf-8")
    (root / "tests/test_keep.py").write_text(KEEP.replace("'ok'", "'broken'"), encoding="utf-8")
    assert verify(task, root).outcome == "regressed"


def test_a_required_test_that_never_ran_is_not_a_pass(upstream):
    """A node that was never collected is not a node that passed."""
    task, root = upstream
    (root / "src/app.py").write_text(FIXED, encoding="utf-8")
    task.source["f2p"] = ["tests/test_new.py::test_never_written"]
    assert verify(task, root).outcome == "unfixed"


def test_a_broken_workspace_is_reported_as_setup_and_not_as_a_failed_task(upstream, tmp_path):
    """Otherwise the harness quietly counts its own breakage against the agent."""
    task, root = upstream
    task.source["repo"] = str(tmp_path / "not-a-repository")
    assert verify(task, root).outcome == "setup"


def test_the_miner_records_a_preservation_set(upstream):
    """E1's other half: nothing could be preserved because nothing was recorded."""
    import tempfile

    from eval import mine

    task, _ = upstream
    repo = Path(task.source["repo"])
    fix = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                         check=True, capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        instance = mine.validate(repo, fix, ["tests/test_new.py"], {}, Path(tmp))
    assert instance is not None
    assert instance.f2p == ["tests/test_new.py::test_double"]
    assert "tests/test_keep.py::test_label" in instance.p2p
    assert not set(instance.p2p) & set(instance.f2p)


# --- E2: the analysis --------------------------------------------------------


def test_repeated_runs_are_all_retained(project):
    """The assertion counts runs, not arms.

    As first written it summed `len(v)` over the per-task values, which counts
    arms — so it failed against the defect and would have gone on failing
    against the fix. A strict xfail that can never xpass is a defect recorded as
    permanently unfixed, which is worse than not recording it at all.
    """
    from eval.analyse import load

    rows = [dict(task="same", arm="vanilla", resolved=value, claimed=True)
            for value in (True, False, True)]
    data = project / "runs.json"
    data.write_text(json.dumps(rows), encoding="utf-8")
    kept = [run for arms in load(data).values() for runs in arms.values() for run in runs]
    assert [r["resolved"] for r in kept] == [True, False, True]


def test_one_pass_per_file_is_enforced_rather_than_assumed(project):
    """`eval.noise` compares two passes; a file of replicates is not a pass."""
    from eval.noise import outcomes

    rows = [dict(task="same", arm="vanilla", resolved=value, claimed=True)
            for value in (True, False)]
    data = project / "runs.json"
    data.write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(ValueError, match="not one pass"):
        outcomes(data, "vanilla")


def test_a_dependency_change_stales_a_suite_result(project):
    """R2's other half, as far as it goes: a lock file is not source, and the
    code depends on it exactly as much."""
    (project / "poetry.lock").write_text('name = "x"\nversion = "1.0"\n', encoding="utf-8")
    evidence = parsers.parse("pytest -q", "1 passed in 0.1s", 0, project)[-1]
    (project / "poetry.lock").write_text('name = "x"\nversion = "2.0"\n', encoding="utf-8")
    assert evidence.freshness(project) is Freshness.STALE
