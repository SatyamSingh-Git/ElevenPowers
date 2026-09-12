"""Every category is decided by the bundle, and every category can be opened.

This project has twice explained a failure from a story rather than from the
run: a null diagnosed from the agent's own test without reading the answer key,
and a conclusion that failures needed information the runtime could not reach
when six of seven were reachable. A taxonomy is the obvious next place for that
to happen, so each category here has to be decidable from evidence, and the
ordering has to be tested — a run that timed out must not also be filed as one
that changed nothing.
"""

from __future__ import annotations

import json

import pytest

from eval.failures import classify, flaky, report

GOLD = ["src/app.py", "src/helpers.py"]
PATCH_RIGHT = "diff --git a/src/app.py b/src/app.py\n@@ -1 +1 @@\n-a\n+b\n"
PATCH_WRONG = "diff --git a/docs/readme.md b/docs/readme.md\n@@ -1 +1 @@\n-a\n+b\n"


def bundle(**over) -> dict:
    base = {
        "manifest": {"task": "t", "arm": "vanilla", "gold": GOLD},
        "answer": {"is_error": False, "terminal_reason": "completed"},
        "grade": {"resolved": False, "outcome": "unfixed", "detail": ""},
        "patch": PATCH_RIGHT,
    }
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = {**base[key], **value}
        else:
            base[key] = value
    return base


def test_a_resolved_run_is_resolved():
    assert classify(bundle(grade={"resolved": True, "outcome": "resolved"})) == "resolved"


def test_harness_breakage_is_never_the_agents_failure():
    assert classify(bundle(grade={"outcome": "setup"})) == "setup"
    assert classify(bundle(grade={"outcome": "timeout"})) == "timeout"


@pytest.mark.parametrize("answer", [
    {"is_error": True},
    {"api_error_status": "overloaded"},
    {"terminal_reason": "max_turns"},
])
def test_a_host_problem_is_told_apart_from_a_wrong_answer(answer):
    assert classify(bundle(answer=answer)) == "host-error"


def test_an_empty_patch_is_its_own_category():
    assert classify(bundle(patch="")) == "no-patch"
    assert classify(bundle(patch="   \n")) == "no-patch"


def test_a_regression_is_not_filed_as_an_ordinary_miss():
    assert classify(bundle(grade={"outcome": "regressed"})) == "regressed"


def test_the_split_that_matters():
    """Found the right code and wrote the wrong change, versus never found it.

    Different problems with different fixes, and nothing in this project
    distinguished them before.
    """
    assert classify(bundle(patch=PATCH_RIGHT)) == "localised"
    assert classify(bundle(patch=PATCH_WRONG)) == "misplaced"


def test_without_a_gold_list_it_refuses_to_guess():
    """Both categories would be a coin flip, so neither is claimed."""
    assert classify(bundle(manifest={"gold": []})) == "unattributed"


def test_order_decides_and_the_first_match_wins():
    """A timed-out run that also changed nothing is a timeout, not a no-patch.

    Without an order, the same run lands in whichever category is checked first,
    and the taxonomy's counts depend on the implementation rather than the run.
    """
    both = bundle(grade={"outcome": "timeout"}, patch="")
    assert classify(both) == "timeout"

    # And a host error outranks the grade, because a turn that never finished
    # says nothing about the patch it did not write.
    assert classify(bundle(answer={"is_error": True}, patch="")) == "host-error"


def test_every_category_cites_bundles_you_can_open(tmp_path, capsys):
    """A category you cannot open is a category you will tell a story about."""
    for name, over in (("one", {"grade": {"resolved": True, "outcome": "resolved"}}),
                       ("two", {"patch": PATCH_WRONG}),
                       ("three", {"grade": {"outcome": "setup"}})):
        directory = tmp_path / name
        directory.mkdir()
        data = bundle(**over)
        (directory / "manifest.json").write_text(json.dumps(data["manifest"]), encoding="utf-8")
        (directory / "answer.json").write_text(json.dumps(data["answer"]), encoding="utf-8")
        (directory / "grade.json").write_text(json.dumps(data["grade"]), encoding="utf-8")
        (directory / "patch.diff").write_text(data["patch"], encoding="utf-8")

    assert report(tmp_path) == 0
    out = capsys.readouterr().out
    for name in ("one", "two", "three"):
        assert name in out, f"{name} is not citable from the report"
    assert "not a distribution" in out, "three runs must not read as a proportion"


def test_a_task_landing_in_two_categories_is_reported_as_variance():
    """Reading one failure of a flaky task as a finding is how noise becomes a diagnosis."""
    found = {
        "resolved": [("a", bundle(manifest={"task": "same"}))],
        "misplaced": [("b", bundle(manifest={"task": "same"}))],
        "no-patch": [("c", bundle(manifest={"task": "other"}))],
    }
    assert flaky(found) == ["same"]


def test_an_empty_directory_says_so(tmp_path, capsys):
    assert report(tmp_path) == 1
    assert "no bundles" in capsys.readouterr().out
