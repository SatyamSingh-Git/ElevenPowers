"""F7 and F12 of the 2026-09-19 audit: what the record cannot say.

Both findings are the same shape as each other and as most of that audit: a
claim stated with more confidence than its evidence carries. "Matched nothing
this task ran" is false if the store is bounded and something fell out of it.
"These attempts are one pool" is false if nothing recorded whether they ran
under the same conditions.

Neither is fixed by keeping more. They are fixed by the claim matching what is
actually known.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from core import assumptions
from core.ledger import Ledger
from eval.pool import condition, measure, pools


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, capture_output=True)
    return tmp_path


# --- F7: a bounded store must not claim to be a complete one ----------------

def test_a_whole_record_says_nothing_extra(repo):
    """Forward. The caveat must be absent when there is nothing to caveat, or
    it is noise on every report and gets ignored on the one that matters."""
    led = Ledger(root=repo, task="t")
    led.saw_output("pytest -q", "1 passed\n")
    assert assumptions.incompleteness(led) == ""
    line = assumptions.wording(["^ok"], [], led)[0]
    assert "partial" not in line


def test_an_evicted_output_is_admitted(repo):
    """Thirteen commands into a twelve-slot store, the first is gone - and the
    check goes on saying "matched nothing this task ran" about a record that no
    longer holds everything the task ran."""
    led = Ledger(root=repo, task="t")
    for i in range(13):
        led.saw_output(f"cmd{i}", f"output {i}\n")
    assert len(led.outputs) == 12
    assert led.outputs_dropped == 1
    said = assumptions.incompleteness(led)
    assert "evicted" in said
    assert "partial" in assumptions.wording(["^ok"], [], led)[0]


def test_a_truncated_output_is_admitted(repo):
    """The other bound. A pattern that would have matched the discarded middle
    is reported as unverified on the strength of a gap."""
    led = Ledger(root=repo, task="t")
    led.saw_output("pytest -q", "head\n" + ("x" * 20000) + "\ntail\n")
    assert led.outputs[0]["truncated"] is True
    assert led.outputs[0]["bytes"] > 20000
    assert "truncated" in assumptions.incompleteness(led)


def test_the_caveat_is_only_attached_to_a_pattern_report(repo):
    """Adversarial: a partial record with nothing to report stays silent."""
    led = Ledger(root=repo, task="t")
    for i in range(13):
        led.saw_output(f"cmd{i}", f"output {i}\n")
    assert assumptions.wording([], [], led) == []


def test_a_ledger_written_before_this_field_existed_still_loads(repo):
    """Adversarial, and the one that breaks users rather than tests.

    `outputs_dropped` is new. A ledger.json from last week has no such key, and
    an upgrade that cannot read yesterday's state is a worse defect than the one
    it fixes.
    """
    from core.ledger import STATE_DIR

    (repo / STATE_DIR).mkdir(parents=True, exist_ok=True)
    (repo / STATE_DIR / "ledger.json").write_text(json.dumps({
        "task": "old", "claims": [], "evidence": [],
        "outputs": [{"command": "pytest", "text": "1 passed"}],
    }), encoding="utf-8")
    back = Ledger.load(repo)
    assert back.task == "old"
    assert back.outputs_dropped == 0
    assert assumptions.incompleteness(back) == "", "an old entry has no truncation flag"


# --- F12: a directory name is not a condition -------------------------------

def _manifest(**over):
    base = {"model_asked": "claude-sonnet-5", "limits": {"agent_seconds": 900,
            "suite_seconds": 900}, "env": {"PYTHONPATH": "src"}}
    base.update(over)
    return base


def test_two_runs_of_the_same_setup_share_a_condition():
    """Forward: identical setups must pool, or nothing ever pools."""
    assert condition(_manifest()) == condition(_manifest())


@pytest.mark.parametrize("difference", [
    {"model_asked": "claude-opus-5"},
    {"limits": {"agent_seconds": 1800, "suite_seconds": 900}},
    {"env": {"PYTHONPATH": "lib"}},
    {"access": {"recorded": True, "registry": "closed"}},
])
def test_a_difference_that_matters_splits_the_condition(difference):
    assert condition(_manifest(**difference)) != condition(_manifest())


def test_unrecorded_access_is_not_the_same_as_open_access():
    """The finding that made this worth building.

    `results/closedbook` is the repository's standing example of a different
    experiment, and its manifest agrees with the open-book sweeps on model,
    limits and task environment - byte for byte. What differed was what the run
    could *reach*, and nothing recorded it. So "nobody wrote it down" has to be
    its own value, distinct from "it was open".
    """
    unrecorded = condition(_manifest())
    known_open = condition(_manifest(access={"recorded": True, "registry": "open"}))
    known_shut = condition(_manifest(access={"recorded": True, "registry": "closed"}))
    assert "access=unrecorded" in unrecorded
    assert unrecorded != known_open != known_shut


def test_a_mixture_of_conditions_is_counted_not_averaged():
    rows = [("s1", "task", "vanilla", "resolved", 1, condition(_manifest())),
            ("s2", "task", "vanilla", "unfixed", 2,
             condition(_manifest(model_asked="claude-opus-5")))]
    got = measure(pools(rows), None, "vanilla")
    assert got["conditions"] == 2, got
    assert got["sweeps"] == 2


def test_one_condition_across_two_sweeps_is_flagged_as_unverifiable():
    """Same model, same limits, same env, two sweeps, nothing recording reach.
    That is the exact shape of the whole existing corpus."""
    rows = [("s1", "task", "vanilla", "resolved", 1, condition(_manifest())),
            ("s2", "task", "vanilla", "unfixed", 2, condition(_manifest()))]
    got = measure(pools(rows), None, "vanilla")
    assert got["conditions"] == 1
    assert got["access_unrecorded"] is True
    assert got["sweeps"] == 2


def test_recorded_access_is_not_flagged():
    """Forward: once a sweep records its reach, the warning must stop."""
    known = condition(_manifest(access={"recorded": True, "registry": "closed"}))
    rows = [("s1", "t", "vanilla", "resolved", 1, known),
            ("s2", "t", "vanilla", "unfixed", 2, known)]
    got = measure(pools(rows), None, "vanilla")
    assert got["access_unrecorded"] is False


def test_a_row_without_a_condition_still_measures():
    """Adversarial: a hand-built five-element row is what every existing test
    and script passes, and it must not start raising."""
    rows = [("s1", "task", "vanilla", "resolved", 1),
            ("s2", "task", "vanilla", "unfixed", 2)]
    got = measure(pools(rows), None, "vanilla")
    assert got["attempts"] == 2
    assert got["conditions"] == 0


# --- the audit's §6: a verdict nobody can attribute -------------------------

def test_a_grade_records_which_grader_produced_it():
    """Regrades are kept side by side; that is half the answer.

    The other half is telling a verdict that changed because the grader changed
    from one that changed because the candidate did - and `grade.json` recorded
    nothing about the grader at all. A content fingerprint needs nobody to
    remember to bump a number.
    """
    from eval.bundle import grader_version

    first = grader_version()
    assert first != "unknown" and len(first) == 16
    assert grader_version() == first, "the same code must fingerprint the same"


def test_the_grader_fingerprint_moves_when_the_grader_does(tmp_path):
    """Forward control. A constant is also stable, and proves nothing."""
    import hashlib
    from pathlib import Path

    import eval.bundle as bundle

    here = Path(bundle.__file__).parent
    before = hashlib.sha256()
    for name in ("live.py", "tasks.py", "bundle.py"):
        assert (here / name).is_file(), f"{name} is named in grader_version and is missing"
        before.update((here / name).read_bytes())
    assert bundle.grader_version() == before.hexdigest()[:16]
