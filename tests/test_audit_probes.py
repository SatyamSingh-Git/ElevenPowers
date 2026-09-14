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
import os
import shutil
import stat
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from core import hook, parsers
from core.config import Config, save as save_config
from core.evidence import (
    Evidence, Freshness, Kind, Result, source_files, tree_hash, vcs_state,
)
from core.ledger import Ledger, Status
from core.obligations import Claim
from core.payload import read_result
from core.repeat import runs_needed
from core.verify import dischargeable
from eval.live import verify


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


def test_deleting_an_observed_file_is_not_verified(project):
    ledger = Ledger(project, claims=[Claim.REFACTOR_SAFE],
                    evidence=[suite_record(project, Result.PASS, 1)])
    (project / "src/app.py").unlink()
    assert ledger.evidence[0].freshness(project) is Freshness.GONE
    assert ledger.status() is not Status.VERIFIED


# --- R4: which record speaks for an identity ---------------------------------

def test_a_failure_after_a_pass_is_not_verified(project):
    ledger = Ledger(project, claims=[Claim.REFACTOR_SAFE], evidence=[
        suite_record(project, Result.FAIL, 1),
        suite_record(project, Result.PASS, 2),
        suite_record(project, Result.FAIL, 3),
    ])
    assert ledger.evidence[-1].result is Result.FAIL
    assert ledger.status() is not Status.VERIFIED


def test_the_same_number_of_different_failures_is_not_tolerated(project):
    """Through the parser, so the per-test records that name the failures exist.

    Hand-built suite records carry a count and a detail string; the question is
    which tests failed, and only a real parse answers it. Timestamps are set
    explicitly because two parses can land in the same clock tick on Windows,
    and the comparison is between the first run and the last.
    """
    before = parsers.parse(
        "pytest -q", "FAILED tests/test_old.py::test_old - assert 0\n"
        "1 failed, 1 passed in 0.1s\n", 1, project)
    after = parsers.parse(
        "pytest -q", "FAILED tests/test_new.py::test_new - assert 0\n"
        "1 failed, 1 passed in 0.2s\n", 1, project)
    for e in before:
        e.at = 1.0
    for e in after:
        e.at = 2.0
    ledger = Ledger(project, claims=[Claim.REFACTOR_SAFE], evidence=before + after)
    assert ledger.status() is not Status.VERIFIED


# --- R5: what counts as having run the suite ---------------------------------

@pytest.mark.parametrize("command,output", [
    ("echo pytest", "pytest\n"),
    ("python -m pytest --version", "pytest 9.1.1\n"),
])
def test_a_command_that_ran_no_tests_is_not_a_passing_suite(project, command, output):
    evidence = parsers.parse(command, output, 0, project)
    ledger = Ledger(project, claims=[Claim.REFACTOR_SAFE], evidence=evidence)
    assert ledger.status() is not Status.VERIFIED


# --- R6: reading is not writing ----------------------------------------------

def test_reading_an_existing_test_is_not_writing_one(project):
    with patch.object(parsers, "vcs_state", return_value=""):
        evidence = parsers.parse("pytest -q", "1 passed in 0.1s", 0, project)
    ledger = Ledger(project, claims=[Claim.BUG_FIXED],
                    seen=["tests/test_app.py"], evidence=evidence)
    assert ledger.status() is not Status.VERIFIED


# --- R7, R8: task identity and risk ------------------------------------------

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


def test_concurrent_writers_do_not_lose_decisions(project):
    Ledger(project, claims=[Claim.BUG_FIXED]).save()
    a, b = Ledger.load(project), Ledger.load(project)
    a.note("event-A", "first worker")
    b.note("event-B", "second worker")
    a.save()
    b.save()
    kept = {d["what"] for d in Ledger.load(project).decisions}
    assert kept == {"event-A", "event-B"}


def test_a_later_sensitive_edit_raises_risk(project):
    ledger = Ledger(project, request="Fix the bug", claims=[Claim.BUG_FIXED])
    ledger.observe_edit("src/auth/session.py")
    assert "src/auth/session.py" in ledger.touched
    assert ledger.risk.value != "low"


# --- R9: what repetition certifies -------------------------------------------

def test_repeating_an_unrelated_command_does_not_certify_stability(project):
    flaky = suite_record(project, Result.FAIL, 1)
    flaky.kind, flaky.identity, flaky.runs, flaky.failed = Kind.STABILITY, "pytest test_worker.py", 10, 1
    unrelated = suite_record(project, Result.PASS, 2)
    unrelated.kind, unrelated.identity, unrelated.runs, unrelated.failed = Kind.STABILITY, "python -c pass", 300, 0
    ledger = Ledger(project, claims=[Claim.BUG_FIXED],
                    request="Fix the flaky test failure", evidence=[flaky, unrelated])
    stability = next(c for c in ledger.verdicts()[0].checks if c.obligation.key == "stable")
    assert not (stability.met and stability.evidence.identity == "python -c pass")


def test_the_run_cap_does_not_overstate_confidence(project):
    rate = 0.001
    needed = runs_needed(rate)
    exact = math.ceil(math.log(0.05) / math.log(1 - rate))
    assert needed >= exact or (1 - rate) ** needed <= 0.05


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
    from eval.live import _seed_git, materialise
    from eval.task import Task

    repo = tmp_path / "upstream"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()
    # `tests/__init__.py` rather than a root conftest: pytest walks up past a
    # package to find the base directory, so the repository root lands on
    # sys.path and `from src.app import ...` resolves. It also leaves
    # `conftest.py` as a name nothing at base owns, which one probe needs.
    for rel, body in ((".gitignore", "__pycache__/\n"), ("src/__init__.py", ""),
                      ("src/app.py", BUGGY), ("tests/__init__.py", ""),
                      ("tests/test_keep.py", KEEP)):
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
    _seed_git(root)
    return task, root


def _erase(root: Path) -> None:
    """Delete a workspace the way losing one feels: completely.

    Git marks its object files read-only and Windows honours that, so a plain
    rmtree stops halfway and the test would be asserting against a tree that is
    still half there.
    """
    def unlock(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    shutil.rmtree(root, onexc=unlock)


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
        instance, why = mine.validate(repo, fix, ["tests/test_new.py"], {}, Path(tmp))
    assert instance is not None, why
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


# --- controls: the fixes must not work by refusing everything ----------------

def test_a_pass_after_a_failure_still_verifies(project):
    """R4's control. The newest record speaks; here the newest one passes."""
    ledger = Ledger(project, claims=[Claim.REFACTOR_SAFE], evidence=[
        suite_record(project, Result.FAIL, 1),
        suite_record(project, Result.PASS, 2),
    ])
    assert ledger.status() is Status.VERIFIED


def test_a_suite_that_really_ran_still_satisfies(project):
    """R5's control. Zero tests is the disqualifier, not the runner's name."""
    evidence = parsers.parse("pytest -q", "2 passed in 0.4s", 0, project)
    ledger = Ledger(project, claims=[Claim.REFACTOR_SAFE], evidence=evidence)
    assert ledger.status() is Status.VERIFIED


def test_writing_a_test_and_a_green_suite_still_counts(project):
    """R6's control, and the one that matters most.

    Cutting `seen` out of that rule is a fix only if the rule still fires for an
    agent that actually wrote the test. Otherwise it is the M1 concession
    deleted, which would put live blocking back where it was before the work
    that brought it from 75 percent of runs to 12.
    """
    (project / "tests/test_new.py").write_text(
        "def test_covers_the_change():\n    assert True\n", encoding="utf-8")
    evidence = parsers.parse("pytest -q", "2 passed in 0.1s", 0, project)
    ledger = Ledger(project, claims=[Claim.BUG_FIXED], request="Fix the bug",
                    touched=["tests/test_new.py"], evidence=evidence)
    met = [c.caveat for c in ledger.verdicts()[0].checks if c.met]
    assert any(c.startswith("a test was written") for c in met), met


# --- H1-H4: the host contract ------------------------------------------------
#
# These four were source findings rather than reproductions: the audit read the
# documented contract and the code, and its script never executed them. So the
# probes are written here rather than derived, and they are written against the
# documented shapes rather than against a replayed transcript — replay fidelity
# is not delivery fidelity, and confusing the two is H1 itself.

def test_a_documented_failure_hook_yields_evidence(project):
    """H1: the documented failure shape puts the error at the top level.

    `read_result` looks only under nested result keys, so this payload produced
    `readable=False`, no evidence, and a blind-spot entry — the runtime going
    quiet against a shape the host is documented to send.
    """
    payload = {
        "hook_event_name": "PostToolUseFailure",
        "tool_name": "Bash",
        "tool_input": {"command": "python -m pytest -q"},
        "error": "Exit code 1\n1 failed in 0.1s",
        "is_interrupt": False,
    }
    result = read_result(payload)
    assert result.readable
    assert result.exit_code == 1
    assert "1 failed" in result.output


def test_a_documented_interrupt_is_skipped_rather_than_scored(project):
    """The same payload's interrupt flag is top-level too."""
    payload = {
        "hook_event_name": "PostToolUseFailure",
        "tool_name": "Bash",
        "tool_input": {"command": "python -m pytest -q"},
        "error": "Exit code 130\n",
        "is_interrupt": True,
    }
    assert read_result(payload).skip == "interrupted"


def test_the_hook_timeout_outlasts_the_verification_it_runs():
    """H2: a callback that dies at twenty seconds cannot run a 300-second suite.

    The host's documented default for a command hook is 600 seconds. The twenty
    was this project's own choice, and it was shorter than the work the hook
    does — a timed-out hook loses its output and makes no decision at all.
    """
    from core.verify import TIMEOUT as VERIFICATION
    from core.wiring import hooks_json

    # The shipped subscription, not the constant: what matters is the number the
    # host is actually told, on the event that does the long work.
    stop = hooks_json()["hooks"]["Stop"][0]["hooks"][0]["timeout"]
    assert stop > VERIFICATION


def test_stop_never_emits_additional_context(project, capsys):
    """H3: Stop does not honour `additionalContext`, so a report sent that way is lost."""
    save_config(project, Config(profile="guide"))
    Ledger(project, request="Fix the bug", claims=[Claim.BUG_FIXED]).save()
    hook.on_stop({"last_assistant_message": "Done."}, project)
    emitted = [json.loads(line) for line in capsys.readouterr().out.splitlines()
               if line.startswith("{")]
    stops = [e["hookSpecificOutput"] for e in emitted
             if e.get("hookSpecificOutput", {}).get("hookEventName") == "Stop"]
    assert stops, "the report-only path should say something"
    assert all("additionalContext" not in s for s in stops)
    assert all(s.get("systemMessage") for s in stops)


def test_powershell_commands_are_seen(project):
    """H4: on Windows the shell tool is called PowerShell, and it was not subscribed."""
    from core.wiring import COMMAND_TOOLS, hooks_json

    assert "PowerShell" in COMMAND_TOOLS
    subscribed = hooks_json()["hooks"]["PostToolUseFailure"][0]["matcher"]
    assert "PowerShell" in subscribed

    hook.on_post_tool({
        "hook_event_name": "PostToolUse",
        "tool_name": "PowerShell",
        "tool_input": {"command": "python -m pytest -q"},
        "tool_response": {"stdout": "2 passed in 0.1s\n", "stderr": ""},
    }, project)
    assert [e for e in Ledger.load(project).evidence if e.kind is Kind.SUITE]


# The other direction for H1-H4. Each probe above asserts the runtime now
# accepts something it used to drop; these assert it still rejects what it
# should. A reader that accepts everything passes every probe above.

def test_an_unreadable_payload_is_still_reported_rather_than_scored(project):
    """H1 forward: widening the reader must not turn a contract change silent.

    The blind-spot log is how the last three defects in this layer were found.
    A reader that answers "fine" to a shape it does not understand is the
    failure mode, not the fix for it.
    """
    result = read_result({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                          "something_new": {"status": "ok"}})
    assert not result.readable


def test_an_empty_error_is_not_read_as_a_passing_command(project):
    """An `error` key present but empty is not evidence that anything passed."""
    result = read_result({"hook_event_name": "PostToolUseFailure",
                          "tool_name": "Bash", "error": ""})
    assert not result.readable or not result.ok


def test_only_the_stop_hook_gets_the_long_timeout():
    """H2 forward: a hook that hangs is worse than one that gives up.

    Stop runs the project's suite. Nothing else does, and a long timeout on
    every event would turn an unrelated failure into a stalled session.
    """
    from core.wiring import TIMEOUT, hooks_json

    for event, entries in hooks_json()["hooks"].items():
        given = entries[0]["hooks"][0]["timeout"]
        assert given == TIMEOUT or event == "Stop", f"{event} got {given}"


def test_a_blocking_stop_still_speaks_through_the_channel_that_blocks(project, capsys):
    """H3 forward: moving the report must not silence the refusal.

    A blocked stop says why on stderr and exits 2. That is a different channel
    from the report, and changing one had every opportunity to break the other.
    """
    save_config(project, Config(profile="strict"))
    Ledger(project, request="Fix the bug", claims=[Claim.BUG_FIXED]).save()
    code = hook.on_stop({"last_assistant_message": "All done."}, project)
    assert code == 2
    assert capsys.readouterr().err.strip()


def test_a_tool_that_is_not_a_shell_produces_no_command_evidence(project):
    """H4 forward: subscribing a second shell must not make every tool a shell."""
    hook.on_post_tool({
        "hook_event_name": "PostToolUse", "tool_name": "WebFetch",
        "tool_input": {"command": "python -m pytest -q"},
        "tool_response": {"stdout": "2 passed in 0.1s\n", "stderr": ""},
    }, project)
    assert not Ledger.load(project).evidence


# --- E3, E5: the run survives, and the evaluator owns the courtroom ----------

def test_the_candidate_survives_its_workspace(upstream, tmp_path):
    """E3: the twelve candidate patches went with their TemporaryDirectory.

    When the grader turned out to be blind to regressions there was nothing
    left to re-grade, so a published null became permanently uncheckable rather
    than merely wrong.
    """
    from eval.bundle import export_patch, read, record_grade, write

    task, root = upstream
    (root / "src/app.py").write_text(FIXED, encoding="utf-8")
    (root / "notes.txt").write_text("scratch\n", encoding="utf-8")

    patch = export_patch(root)
    assert "def double(n):" in patch and "notes.txt" in patch, "new files count too"

    kept = write(tmp_path / "bundles" / "run", task=task.name, arm="vanilla",
                 model="claude-opus-5", asked="opus", patch=patch,
                 answer={"num_turns": 3}, limits={"agent_seconds": 900},
                 ledger=None, source=task.source)
    record_grade(kept, verify(task, root))

    # The workspace is gone; the run is not.
    _erase(root)
    back = read(kept)
    assert back["patch"] == patch
    assert back["manifest"]["required"]["p2p"] == ["tests/test_keep.py::test_label"]
    assert back["manifest"]["model"] == "claude-opus-5"
    assert back["grade"]["resolved"] is True
    assert back["grade"]["passed"] == ["tests/test_keep.py::test_label",
                                       "tests/test_new.py::test_double"]


def test_a_preserved_patch_regrades_to_the_same_answer(upstream, tmp_path):
    """E3 forward: a bundle nobody can re-grade from is a receipt, not evidence."""
    from eval.bundle import export_patch
    from eval.live import grade_patch

    task, root = upstream
    (root / "src/app.py").write_text(FIXED.replace("'ok'", "'broken'"), encoding="utf-8")
    patch = export_patch(root)
    _erase(root)

    again = grade_patch(task, patch, tmp_path / "court")
    assert again.outcome == "regressed"


def test_grading_ignores_what_the_patch_does_not_carry(upstream, tmp_path):
    """E5: the grade is a function of the base and the patch, and nothing else.

    A workspace holds more than a patch does — ignored build output, an
    editable install, anything the agent did outside the repository. Grading
    inside it makes the verdict depend on state no bundle preserves and no
    second opinion can reconstruct, which is what "separation in time is not
    isolation of authority" means in practice.

    The lever here is an ignored `conftest.py`; it stands for all of that. In
    its own tree the agent's patch looks resolved. Graded from the patch in a
    tree the evaluator built, the regression is visible.
    """
    from eval.bundle import export_patch
    from eval.live import grade_patch

    task, root = upstream
    (root / "src/app.py").write_text(FIXED.replace("'ok'", "'broken'"), encoding="utf-8")
    (root / ".gitignore").write_text("__pycache__/\nconftest.py\n", encoding="utf-8")
    (root / "conftest.py").write_text(
        "import src.app\n\nsrc.app.label = lambda: 'ok'\n", encoding="utf-8")

    assert verify(task, root).resolved, "in its own tree the workspace answers for itself"

    patch = export_patch(root)
    assert "conftest.py" not in patch or "src.app.label" not in patch
    assert grade_patch(task, patch, tmp_path / "court").outcome == "regressed"


# --- E4, E6: an arm that is present, and a bound that holds -------------------

def test_a_missing_plugin_stops_the_run_instead_of_relabelling_vanilla():
    """E4: an arm named for a plugin that is not installed ran as vanilla.

    It was still recorded under the plugin's name, so a comparison between two
    identical configurations would have been reported as a composition result.
    """
    from eval.live import PLUGINS, _plugin_dir

    PLUGINS["superpowers"] = ""
    with pytest.raises(SystemExit, match="EP_SUPERPOWERS_DIR"):
        _plugin_dir("superpowers")


def test_a_present_plugin_is_used(tmp_path):
    """E4 forward: refusing every arm is not a fix."""
    from eval.live import PLUGINS, _plugin_dir

    (tmp_path / "plugin").mkdir()
    PLUGINS["superpowers"] = str(tmp_path / "plugin")
    assert _plugin_dir("superpowers") == str(tmp_path / "plugin")


def test_the_run_records_the_environment_it_happened_in():
    """E4: an inherited environment is not a controlled one, and was not recorded."""
    from eval.live import environment

    seen = environment()
    assert seen["python"] and seen["platform"]


def test_arm_order_is_not_fixed():
    """E4: a fixed order confounds the arm with anything that drifts mid-sweep.

    Against `eval.live`'s own ordering rather than against `random.shuffle`: a
    test of the standard library would pass whether or not the sweep used it.
    """
    import random

    from eval.live import arm_order

    arms = ["vanilla", "nudge", "guide", "gate"]
    seen = {tuple(arm_order(arms, random.Random(seed))) for seed in range(40)}
    assert len(seen) > 1
    assert all(sorted(order) == sorted(arms) for order in seen), "every arm still runs"


def test_the_run_count_is_not_derived_from_the_flip_rate():
    """E6: flipping is within one arm, disagreement is between two.

    A baseline that fails every time against a treatment that succeeds every
    time flips never and disagrees always, so dividing by the flip rate gave a
    run count with nothing behind it — and the smaller the flip rate, the more
    confident the wrong answer looked.
    """
    from eval.noise import discordant_pairs_needed, runs_for

    pairs = discordant_pairs_needed()
    assert pairs > 0
    # Total disagreement needs exactly the pairs, whatever anything flips.
    assert runs_for(1.0) == pairs
    assert runs_for(0.5) == 2 * pairs
    assert runs_for(0.0) == 0


def test_the_candidate_is_the_code_and_not_the_workspace_noise(upstream):
    """A live run made every exported patch mostly compiled bytecode.

    The seeded workspace had no ignore rules, so `git add -A` staged
    `__pycache__`, the pytest cache and the runtime's own ledger. `git apply`
    then rejected the whole patch over the binary entries, and all four runs
    came back as `setup` — correctly, since it was the harness that broke, but
    the candidate was not the agent's answer either way.
    """
    from eval.bundle import export_patch

    task, root = upstream
    (root / "src/app.py").write_text(FIXED, encoding="utf-8")
    for rel in ("src/__pycache__/app.cpython-313.pyc", ".pytest_cache/v/cache/lastfailed",
                ".elevenpowers/ledger.json"):
        noise = root / rel
        noise.parent.mkdir(parents=True, exist_ok=True)
        noise.write_bytes(b"\x00\x01not the answer\x00")

    patch = export_patch(root)
    assert "src/app.py" in patch
    for unwanted in ("__pycache__", ".pytest_cache", ".elevenpowers"):
        assert unwanted not in patch, f"{unwanted} is workspace noise, not a candidate"


def test_the_model_recorded_is_the_one_the_host_used():
    """E4: the alias was being recorded while the docstring claimed otherwise.

    The shape below is from a real `claude --output-format json` answer: there
    is no top-level `model` key, so reading one fell back to the alias every
    time and nothing said so. Usage is reported per concrete model id.
    """
    from eval.live import resolved_model

    answer = {"modelUsage": {"claude-haiku-4-5-20251001": {"costUSD": 0.11}},
              "num_turns": 16}
    assert resolved_model(answer, "haiku") == "claude-haiku-4-5-20251001"
    # A host that reports no usage leaves the alias, which is honest: it is all
    # there is. It must not invent a resolution.
    assert resolved_model({"num_turns": 3}, "haiku") == "haiku"


def test_a_seeded_task_records_which_tests_were_seen_to_pass():
    """A verdict with nothing behind it is the failure this slice is about.

    Every bundle from the simple suite carried `passed: []`, because the seeded
    grader never filled in the node outcomes the real-task one does.
    """
    import tempfile

    from eval.live import build, verify
    from eval.tasks import by_name

    task = by_name("last_page")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        root = Path(tmp)
        build(task, root, arm="vanilla")
        graded = verify(task, root)
        assert not graded.resolved, "the seeded bug is still there"
        assert any(n.startswith("tests/") for n in graded.observed), graded.observed


# --- the grader corrupted every patch it was handed, and got away with it ----

def test_a_saved_patch_is_byte_identical_to_the_one_exported(upstream, tmp_path):
    """`write_text` translates newlines, so every bundle held a CRLF patch.

    The existing round-trip probe asserts `read(bundle)["patch"] == patch` and
    passed throughout, because `read_text` translates the damage back out again.
    A file written and read by the same library agrees with itself no matter
    what it put on disk; only the bytes say what a bundle actually contains.
    """
    from eval.bundle import export_patch, write

    task, root = upstream
    (root / "src/app.py").write_bytes(FIXED.encode("utf-8"))
    patch = export_patch(root)

    kept = write(tmp_path / "b" / "run", task=task.name, arm="vanilla",
                 model="claude-opus-5", asked="opus", patch=patch,
                 answer={"num_turns": 3}, limits={}, ledger=None,
                 source=task.source)

    assert (kept / "patch.diff").read_bytes() == patch.encode("utf-8")


def test_the_patch_reaching_git_is_the_patch_that_was_exported(upstream, tmp_path,
                                                               monkeypatch):
    """A text pipe translates on the way in as well as on the way out.

    `git apply` tolerates a carriage return on every line for some hunks and
    not others, so this bought two live runs on real repositories that passed
    while a third could not apply its patch at all. Asserting that the patch
    applies would have passed before the fix; the bytes are the claim.
    """
    import subprocess

    from eval.bundle import export_patch
    from eval.live import grade_patch

    task, root = upstream
    # Bytes, so the fixture does not put a carriage return in the file and
    # then get blamed for one. `write_text` translates on Windows exactly
    # as the code under test did, which would make this assertion a
    # statement about pytest's tmp_path.
    (root / "src/app.py").write_bytes(FIXED.encode("utf-8"))
    patch = export_patch(root)
    assert "\r" not in patch, "git did not put one there"

    handed = []
    unwatched = subprocess.run

    def watch(command, **kw):
        if "apply" in command:
            handed.append(kw.get("input"))
        return unwatched(command, **kw)

    monkeypatch.setattr("eval.bundle.subprocess.run", watch)
    graded = grade_patch(task, patch, tmp_path / "court")

    assert handed and isinstance(handed[0], bytes), (
        "a text pipe: Python translates every newline on the way into the child, "
        "so git receives carriage returns this patch does not contain")
    assert handed == [patch.encode("utf-8")]
    assert graded.outcome == "resolved", "the byte check must not come at the cost of the grade"


# --- an agent uninstalled a package from under the next task ------------------

def test_a_run_that_collected_nothing_is_not_the_agents_fault(upstream, tmp_path,
                                                              monkeypatch):
    """Twelve runs were scored against the agent for a missing dependency.

    One agent ran `pip install -e .` in its temp workspace; pip wrote a .pth into
    the shared user site pointing at that directory, and when the workspace was
    deleted `import attrs` broke machine-wide. Every later task whose tests
    import trio collected nothing, and every one of those runs was filed as the
    agent having failed to fix the bug. The taxonomy already promised that
    harness breakage is "never the agent"; the code had no way to tell.
    """
    from eval.live import grade_patch

    task, root = upstream
    # A conftest the evaluator restores with the test tree, so the failure is at
    # import time and belongs to the environment, exactly as a missing package
    # would be -- and it is there for the base commit too.
    (Path(task.source["repo"]) / "tests" / "conftest.py").write_bytes(
        b"import a_package_that_is_not_installed\n")
    import subprocess
    subprocess.run(["git", "-C", task.source["repo"], "add", "-A"],
                   capture_output=True)
    subprocess.run(["git", "-C", task.source["repo"], "-c", "user.email=e@e",
                    "-c", "user.name=e", "commit", "-qm", "break the environment"],
                   capture_output=True)
    task.source["base"] = subprocess.run(
        ["git", "-C", task.source["repo"], "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()

    graded = grade_patch(task, "", tmp_path / "court")

    assert graded.outcome == "setup", (
        "a run where nothing collected and the base does not collect either is "
        "the harness, and the score excludes setup from the agent's record")


def test_an_agent_that_breaks_the_module_is_still_the_agents_fault(upstream, tmp_path):
    """The forward direction, and the one the control exists to protect.

    An agent that breaks a module and a machine missing a dependency both
    observe nothing. A check that blamed the harness for both would excuse every
    candidate that failed to import, which is worse than the defect it fixes.
    """
    from eval.bundle import export_patch
    from eval.live import grade_patch

    task, root = upstream
    (root / "src/app.py").write_bytes(b"syntax ( error\n")
    patch = export_patch(root)

    graded = grade_patch(task, patch, tmp_path / "court")

    assert graded.outcome == "unfixed", graded.detail


def test_the_agents_package_manager_cannot_touch_the_shared_site(tmp_path):
    """Run against real pip, because reasoning about this has been wrong twice.

    An agent installed into the shared user site and broke `import attrs`
    machine-wide, costing twelve graded runs. `PIP_PREFIX` was the fix. Four
    runs later another agent **uninstalled attrs**, which `PIP_PREFIX` says
    nothing about -- it steers where a package is written, not where one is
    removed from. `PIP_REQUIRE_VIRTUALENV` refuses both.

    Every repository in the corpus is also installed in the environment that
    grades it, so this is not an exotic failure: an agent working on attrs is
    one `pip uninstall` from the grader's own dependency.
    """
    import glob
    import site
    import subprocess
    import sys

    from eval.live import _sandboxed

    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_bytes(
        b'[project]\nname = "ep-probe-pkg"\nversion = "0.0.1"\n')

    shared = site.getusersitepackages()
    before = set(glob.glob(shared + "/*"))
    environment = _sandboxed(project)

    for command in (["install", "-e", "."], ["uninstall", "-y", "attrs"]):
        done = subprocess.run([sys.executable, "-m", "pip", *command],
                              cwd=project, env=environment, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=300)
        assert done.returncode != 0, f"pip {command[0]} was allowed to run"

    assert set(glob.glob(shared + "/*")) == before
    import importlib.util
    assert importlib.util.find_spec("attrs"), "attrs was removed from the machine"


def test_a_run_whose_environment_changed_is_not_the_agents_fault(upstream, tmp_path,
                                                                 monkeypatch):
    """A removal, not an addition, which is what the first detector missed.

    It compared the shared site for *new* entries only. The second
    contamination deleted `attrs`, so the check saw nothing, and thirty-eight
    corpus instances silently stopped rebuilding. The comparison is symmetric
    now, and a run whose environment moved underneath it is graded `setup` --
    harness breakage, never counted against the agent, because the alternative
    is what pass B did: turn solved tasks into failures and a changed version
    string into a regression.
    """
    import eval.live

    task, root = upstream
    (root / "src/app.py").write_bytes(FIXED.encode("utf-8"))

    monkeypatch.setattr(eval.live, "drive",
                        lambda *a, **k: ({"result": "done", "num_turns": 1}, 1.0))
    sites = iter([frozenset({"attrs", "trio"}), frozenset({"trio"})])
    monkeypatch.setattr(eval.live, "shared_site", lambda: next(sites))
    monkeypatch.setattr(eval.live, "build", lambda t, r, a: shutil.copytree(
        root, r, dirs_exist_ok=True))

    run = eval.live.once(task, "vanilla", "claude-sonnet-5")

    assert run.outcome == "setup", "a patch graded in a different environment"
    assert "attrs" in run.note, run.note
    assert run.resolved is False


def test_an_untouched_environment_grades_the_patch_normally(upstream, tmp_path,
                                                            monkeypatch):
    """The forward direction. A guard that fires when nothing moved would mark
    every run as harness breakage and the sweep would score nothing at all.
    """
    import eval.live

    task, root = upstream
    (root / "src/app.py").write_bytes(FIXED.encode("utf-8"))

    monkeypatch.setattr(eval.live, "drive",
                        lambda *a, **k: ({"result": "done", "num_turns": 1}, 1.0))
    monkeypatch.setattr(eval.live, "shared_site", lambda: frozenset({"attrs", "trio"}))
    monkeypatch.setattr(eval.live, "build", lambda t, r, a: shutil.copytree(
        root, r, dirs_exist_ok=True))

    run = eval.live.once(task, "vanilla", "claude-sonnet-5")

    assert run.outcome == "resolved", run.note


def _alive(pid: int) -> bool:
    import subprocess
    import sys

    if sys.platform == "win32":
        done = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace")
        return str(pid) in (done.stdout or "")
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def test_nothing_the_agent_spawned_outlives_the_run(tmp_path):
    """An orphan cannot be killed by walking down from its parent.

    An agent looking for a file runs `find / -iname sandbox.py`, which walks the
    whole drive. When the agent exits with that search still going the search is
    orphaned, and `subprocess.run` never knew about it in the first place.
    Eleven accumulated across two paid chunks and took ninety percent of the
    machine; by the time they were noticed no process tree led to them.

    So this spawns a grandchild, lets the child exit immediately, and asks
    whether the grandchild is still running afterwards. Containment has to be
    arranged before the work starts, which is why the fix is a job object rather
    than a tidy-up.
    """
    import sys
    import time

    from eval.live import contained

    marker = tmp_path / "grandchild.pid"
    # DEVNULL, so this measures the job object rather than pipe inheritance:
    # a grandchild holding the parent's stdout keeps communicate() waiting on
    # its own account, which is a different defect with a different fix.
    inner = (
        "import os, sys, time; "
        "open(sys.argv[1], \"w\").write(str(os.getpid())); "
        "time.sleep(300)"
    )
    spawn = (
        "import os, subprocess, sys, time;"
        "subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2]],"
        " stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,"
        " stdin=subprocess.DEVNULL);"
        # Wait until it has recorded itself, then leave: the point is a child
        # that exits while its own child is still going, which is how the
        # `find /` searches came to have no parent left to walk down from.
        "[time.sleep(0.05) for _ in range(200) if not os.path.exists(sys.argv[2])]"
    )

    out, err, timed_out = contained(
        [sys.executable, "-c", spawn, inner, str(marker)], tmp_path,
        dict(os.environ), 60)

    assert not timed_out, err
    for _ in range(50):
        if marker.exists():
            break
        time.sleep(0.1)
    assert marker.exists(), "the grandchild never started, so this proves nothing"
    stray = int(marker.read_text().strip())

    time.sleep(1)
    assert not _alive(stray), f"process {stray} outlived the run"
