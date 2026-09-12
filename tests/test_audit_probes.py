"""The sixteen defects an external audit reproduced, as tests.

Each test asserts the behaviour the system is supposed to have, and is marked
`xfail(strict=True)` because it does not have it yet. That choice is deliberate:
the suite stays green so ordinary work is not drowned in noise, the defects are
recorded as known rather than forgotten, and the moment one is fixed its test
turns from xfail to xpass and **fails the run**, which forces the marker off.

A defect that lives in a document is a note. A defect that lives here cannot be
quietly un-fixed.

Source: `docs/research/audit_2026_09_11/`. Identifiers match PLAN.md section 4.
"""

from __future__ import annotations

import contextlib
import io
import json
import math
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from core import hook, parsers
from core.config import Config
from core.evidence import Evidence, Freshness, Kind, Result, source_files, tree_hash, vcs_state
from core.ledger import Ledger, Status
from core.obligations import Claim
from core.repeat import runs_needed
from core.verify import dischargeable

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

@defect("R1", "size and mtime with a vcs_state tie-breaker; two contents share one porcelain status")
def test_changing_an_already_dirty_file_stales_its_evidence(committed):
    """The whole promise is that editing a file invalidates what depended on it.

    `vcs_state` is pinned because the defect lives only in the branch where git
    resolves: an unpinned version of this passed alone and failed in the full
    suite, since git's path form does not always match `tmp_path` on Windows and
    an empty `vcs_state` hides the bug rather than fixing it.
    """
    app = committed / "src/app.py"
    app.write_text("value = 1\n", encoding="utf-8")
    # Both bindings: `parsers` imported the name, so patching only the module it
    # came from leaves the two calls disagreeing and hides the defect.
    with patch("core.evidence.vcs_state", return_value="pinned"), \
         patch("core.parsers.vcs_state", return_value="pinned"):
        evidence = parsers.parse("pytest -q", "1 passed in 0.1s", 0, committed)[-1]
        app.write_text("value = 999\n", encoding="utf-8")
        assert evidence.freshness(committed) is Freshness.STALE


@defect("R2", "observed is a stored list, so files that did not exist cannot appear in it")
def test_adding_a_test_file_stales_a_suite_result(project):
    evidence = suite_record(project, Result.PASS, 1)
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


# --- E1, E2: the evaluator ---------------------------------------------------

@defect("E1", "the grader runs only the fail-to-pass set; there is no preservation set")
def test_the_grader_runs_a_preservation_set(project):
    from eval.live import _verify_real
    from eval.task import Task

    task = Task(name="audit", prompt="Fix it", files={}, hidden="", why="audit",
                source={"hidden_files": {}, "f2p": ["tests/test_new.py::test_requested"], "env": {}})
    done = subprocess.CompletedProcess([], 0, "", "")
    with patch("eval.live.subprocess.run", return_value=done) as ran:
        _verify_real(task, project)
    invoked = " ".join(str(a) for a in ran.call_args.args[0])
    assert "p2p" in invoked or invoked.count("::") == 0, (
        "grading must also run tests that were passing and must stay passing")


@defect("E2", "analyse keeps one row per task and arm, so replicates overwrite each other")
def test_repeated_runs_are_all_retained(project):
    from eval.analyse import load

    rows = [dict(task="same", arm="vanilla", resolved=value, claimed=True)
            for value in (True, False, True)]
    data = project / "runs.json"
    data.write_text(json.dumps(rows), encoding="utf-8")
    assert sum(len(v) for v in load(data).values()) == len(rows)
