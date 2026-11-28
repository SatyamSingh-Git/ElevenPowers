"""Mutation score on an agent patch's changed lines, with the real Cosmic Ray generator."""
import pytest

from tests.test_heldout_transfer import _patch
from tests.test_heldout_grading import _task

PINS = "from pkg.mod import value\n\n\ndef test_two():\n    assert value() == 2\n"
RED = "def test_unrelated():\n    assert False\n"


def _score(tmp_path, source, tests):
    pytest.importorskip("cosmic_ray")
    from eval import heldout_mutation as m
    task, _ = _task(tmp_path)
    return m.score(task, _patch(task, tmp_path, source, tests), tmp_path / "work")


def test_a_test_of_the_changed_line_kills_its_mutants(tmp_path):
    value = _score(tmp_path, "def value():\n    return 2\n", {"test_agent.py": PINS})
    assert value["outcome"] == "scored" and value["mutants"] >= 1
    assert value["killed"] == value["mutants"]


def test_without_one_the_existing_suite_lets_them_live(tmp_path):
    # test_old only asserts value() > 0, which 2 + 1 and 2 - 1 both satisfy.
    value = _score(tmp_path, "def value():\n    return 2\n", {})
    assert value["outcome"] == "scored" and value["mutants"] >= 1 and value["killed"] == 0


def test_a_test_already_red_on_the_patch_does_not_kill_anything(tmp_path):
    value = _score(tmp_path, "def value():\n    return 2\n", {"test_red.py": RED})
    assert value["outcome"] == "scored" and value["killed"] == 0


def test_a_change_no_operator_reaches_has_no_mutant(tmp_path):
    value = _score(tmp_path, "def value():\n    return 1\n\n\nNAME = 'two'\n", {})
    assert value["outcome"] == "no mutant"


def test_the_analysis_runs_the_five_pairs_over_task_means_with_holm():
    from eval import heldout_mutation as m
    from eval.heldout_analyse import PAIRS, holm
    rows = [{"task": "a", "arm": "ordinary", "outcome": "scored", "mutants": 4, "killed": 1},
            {"task": "a", "arm": "ordinary", "outcome": "scored", "mutants": 2, "killed": 2},
            {"task": "a", "arm": "instructed", "outcome": "scored", "mutants": 4, "killed": 4},
            {"task": "b", "arm": "ordinary", "outcome": "scored", "mutants": 2, "killed": 0},
            {"task": "b", "arm": "instructed", "outcome": "scored", "mutants": 2, "killed": 1},
            {"task": "b", "arm": "assisted", "outcome": "no mutant", "mutants": 0, "killed": 0},
            {"task": "c", "arm": "assisted", "outcome": "scored", "mutants": 1, "killed": 1}]
    value = m.analyse(rows)
    pair = value["primary"]["ordinary - instructed"]
    # Task a: ordinary's runs score 0.25 and 1.0, a mean of 0.625; instructed 1.0.
    assert pair["differences"] == {"a": -0.375, "b": -0.5} and pair["tied"] == 0
    assert value["primary"]["ordinary - assisted"]["differences"] == {}
    raw = [value["primary"][f"{a} - {b}"]["p"] for a, b in PAIRS]
    assert [value["primary"][f"{a} - {b}"]["holm_p"] for a, b in PAIRS] == holm(raw)
    assert value["per_arm"]["assisted"] == {"runs": 2, "scored": 1, "no_mutant": 1, "mutants": 1, "killed": 1}
    assert value["per_arm"]["ordinary"]["mutants"] == 8 and value["per_arm"]["ordinary"]["killed"] == 3


def test_only_the_changed_lines_are_mutated_and_the_tree_is_restored(tmp_path, monkeypatch):
    # Line 2 is the change; line 3 is the original `return 1`, now in the changed function.
    # Cosmic Ray lists line 2's nine candidates first, so the limit must reach past them.
    pytest.importorskip("cosmic_ray")
    from eval import heldout_mutation as m
    monkeypatch.setattr(m, "RUN", 16)
    source = "def value():\n    flag = 2 > 1\n    return 1\n"
    value = _score(tmp_path, source, {})
    assert value["outcome"] == "scored"
    assert {line for _, line, _, _ in value["operators"]} == {2}
    assert (tmp_path / "work" / "tree" / "pkg" / "mod.py").read_text(encoding="utf8") == source


def test_a_mutant_that_times_out_or_errors_without_a_failed_line_is_killed(tmp_path, monkeypatch):
    pytest.importorskip("cosmic_ray")
    from eval import heldout_mutation as m
    runs = iter([(set(), False, 0), (set(), True, -1), (set(), False, 2)])
    monkeypatch.setattr(m, "_suite", lambda *a, **k: next(runs, (set(), False, 0)))
    monkeypatch.setattr(m, "RUN", 2)
    task, _ = _task(tmp_path)
    value = m.score(task, _patch(task, tmp_path, "def value():\n    return 2\n", {}), tmp_path / "work")
    assert (value["mutants"], value["killed"]) == (2, 2)
