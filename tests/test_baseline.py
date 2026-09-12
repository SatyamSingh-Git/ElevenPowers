"""A score is a claim about a benchmark, a model and an amount of luck.

Each of those three has gone wrong here before: the corpus was whatever had been
mined that week, the model was an alias that could point somewhere else
tomorrow, and the number was a bare percentage. So the refusals are tested as
carefully as the arithmetic, and in both directions — a harness that refuses
everything is not pinned, it is broken.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import pytest

from eval.baseline import (
    compare, corpus_fingerprint, interval, is_alias, read_journal,
    reached_the_model, run_baseline, score,
)
from eval.live import Run
from eval.task import Task
from eval.live import context_tokens


def rows(pattern: dict[str, list[bool]], **extra) -> list[dict]:
    return [{"task": name, "arm": "vanilla", "claimed": True, "resolved": ok,
             "outcome": "resolved" if ok else "unfixed", **extra}
            for name, outcomes in pattern.items() for ok in outcomes]


# --- what pinned refuses, and what it must not refuse ------------------------

@pytest.mark.parametrize("model,alias", [
    ("haiku", True), ("sonnet", True), ("opus", True),
    ("claude-haiku-4-5-20251001", False), ("claude-opus-5", False),
])
def test_an_alias_is_told_apart_from_a_version(model, alias):
    """The host resolves an alias at request time.

    Two sweeps a month apart can therefore run different models and report one
    number, which is exactly what the bundle manifest was doing until a live run
    exposed it.
    """
    assert is_alias(model) is alias


def test_the_corpus_fingerprint_changes_when_the_corpus_does(tmp_path):
    lock = tmp_path / "corpus.lock"
    pins = [{"name": "a", "origin": "u", "base": "b", "fix": "f"}]
    lock.write_text(json.dumps(pins), encoding="utf-8")
    before = corpus_fingerprint(lock)

    lock.write_text(json.dumps(pins + [{"name": "b", "origin": "u", "base": "c",
                                        "fix": "g"}]), encoding="utf-8")
    assert corpus_fingerprint(lock) != before

    two = corpus_fingerprint(lock)

    # Order must not matter: the same instances mined in a different sequence
    # are the same benchmark, and a fingerprint that disagreed would forbid a
    # reproduction that is perfectly valid. Comparing the file with itself would
    # assert nothing, which is how this check was first written.
    lock.write_text(json.dumps(list(reversed(json.loads(lock.read_text(encoding="utf-8"))))),
                    encoding="utf-8")
    assert corpus_fingerprint(lock) == two


def test_a_missing_lock_fingerprints_as_nothing(tmp_path):
    assert corpus_fingerprint(tmp_path / "absent.lock") == ""


# --- the interval ------------------------------------------------------------

def test_replicates_of_one_task_do_not_narrow_the_interval():
    """The correction that matters, and the one E2 already forced once.

    Fifteen tasks at three replicates is forty-five numbers and nowhere near
    forty-five independent ones. Resampling runs would shrink the interval by
    about sqrt(3) and make an honest rerun look like a contradiction.
    """
    tasks = {f"t{i}": [i % 2 == 0] for i in range(10)}
    one = interval([statistics.fmean(v) for v in tasks.values()], seed=7)

    tripled = {name: outcomes * 3 for name, outcomes in tasks.items()}
    three = interval([statistics.fmean(v) for v in tripled.values()], seed=7)

    assert one == three, "replicates of the same tasks add no independent information"


def test_the_interval_widens_as_tasks_are_removed():
    wide = interval([1.0, 0.0, 1.0, 0.0], seed=3)
    narrow = interval([1.0, 0.0] * 30, seed=3)
    assert (wide[1] - wide[0]) > (narrow[1] - narrow[0])


def test_one_task_bounds_nothing_and_says_so():
    assert interval([1.0], seed=1) == (0.0, 1.0)


def test_the_interval_is_reproducible_from_its_seed():
    per_task = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
    assert interval(per_task, seed=11) == interval(per_task, seed=11)


def test_a_setup_failure_is_counted_apart_from_a_wrong_answer():
    """Harness breakage is not evidence about the agent."""
    data = rows({"a": [True], "b": [False]})
    data.append({"task": "c", "arm": "vanilla", "claimed": True, "resolved": False,
                 "outcome": "setup"})
    assert score(data, seed=1)["setup_failures"] == 1


# --- what reached the model --------------------------------------------------

def test_context_is_measured_from_cache_creation_not_cache_reads():
    """Read tokens grow with turns and say nothing about what was installed.

    Taken from a real `claude --output-format json` answer: 584,272 read tokens
    against 14,935 created. Using the larger number would report a talkative run
    as a heavily configured one.
    """
    answer = {"modelUsage": {"claude-haiku-4-5-20251001": {
        "inputTokens": 123, "cacheCreationInputTokens": 14935,
        "cacheReadInputTokens": 584272}}}
    assert context_tokens(answer) == 15058


def test_an_arm_that_loaded_nothing_is_visible_in_the_context(tmp_path):
    """E4's missing measurement: an absent plugin used to look like a null result."""
    plain = reached_the_model(rows({"a": [True]}, context_tokens=15_000))
    loaded = reached_the_model(rows({"a": [True]}, context_tokens=38_000))
    assert plain["median"] < loaded["median"]
    assert reached_the_model(rows({"a": [True]})) == {}


# --- reproduction ------------------------------------------------------------

def write(path: Path, resolved: float, low: float, high: float, **over) -> Path:
    path.write_text(json.dumps({
        "model": over.get("model", "claude-haiku-4-5-20251001"),
        "corpus": over.get("corpus", "abc123"),
        "seed": 1,
        "score": {"tasks": 15, "runs": 45, "resolved": resolved, "low": low,
                  "high": high, "setup_failures": 0, "context": {}},
    }), encoding="utf-8")
    return path


def test_a_rerun_inside_the_interval_reproduces(tmp_path, capsys):
    a = write(tmp_path / "a.json", 0.40, 0.20, 0.60)
    b = write(tmp_path / "b.json", 0.47, 0.27, 0.67)
    assert compare(a, b) == 0
    assert "reproduces" in capsys.readouterr().out


def test_a_rerun_outside_the_interval_does_not(tmp_path):
    a = write(tmp_path / "a.json", 0.40, 0.35, 0.45)
    b = write(tmp_path / "b.json", 0.80, 0.75, 0.85)
    assert compare(a, b) == 1


def test_two_corpora_are_refused_however_close_the_scores(tmp_path, capsys):
    """The refusal pinning exists for.

    Identical numbers from two different benchmarks are not a reproduction, and
    this is the comparison somebody makes by accident after re-mining.
    """
    a = write(tmp_path / "a.json", 0.40, 0.20, 0.60, corpus="abc123")
    b = write(tmp_path / "b.json", 0.40, 0.20, 0.60, corpus="def456")
    assert compare(a, b) == 1
    assert "not a reproduction" in capsys.readouterr().out


def test_two_models_are_refused(tmp_path):
    a = write(tmp_path / "a.json", 0.4, 0.2, 0.6, model="claude-haiku-4-5-20251001")
    b = write(tmp_path / "b.json", 0.4, 0.2, 0.6, model="claude-opus-5")
    assert compare(a, b) == 1


def test_pinned_refuses_each_way_it_can_be_unpinned(tmp_path, monkeypatch):
    from eval.baseline import refusals

    lock = tmp_path / "corpus.lock"
    lock.write_text(json.dumps([{"name": "a", "origin": "u", "base": "b", "fix": "f"}]),
                    encoding="utf-8")
    monkeypatch.setattr("eval.baseline.working_tree_clean", lambda _: True)

    assert any("alias" in r for r in refusals("haiku", lock, tmp_path))
    assert any("--model is required" in r for r in refusals("", lock, tmp_path))
    assert any("no corpus lock" in r
               for r in refusals("claude-haiku-4-5-20251001", tmp_path / "gone", tmp_path))

    monkeypatch.setattr("eval.baseline.working_tree_clean", lambda _: False)
    assert any("dirty" in r for r in refusals("claude-haiku-4-5-20251001", lock, tmp_path))


def test_pinned_accepts_a_run_that_is_actually_pinned(tmp_path, monkeypatch):
    """The forward direction. A harness that refuses everything is not pinned."""
    from eval.baseline import refusals

    lock = tmp_path / "corpus.lock"
    lock.write_text(json.dumps([{"name": "a", "origin": "u", "base": "b", "fix": "f"}]),
                    encoding="utf-8")
    monkeypatch.setattr("eval.baseline.working_tree_clean", lambda _: True)
    assert refusals("claude-haiku-4-5-20251001", lock, tmp_path) == []


def test_a_task_of_unknown_size_is_not_filed_under_a_band():
    """Silently bucketing it would make the table look complete and say nothing.

    A missing size defaulted to zero lands in "empty", so one mismatched name
    between the run and the corpus would quietly relabel the whole report.
    """
    from eval.baseline import bands_of

    data = rows({"known": [True, True], "mystery": [False]})
    out = bands_of(data, {"known": 2})
    assert out["one-liner"] == {"tasks": 1, "resolved": 1.0}
    assert out["unknown"] == {"tasks": 1, "resolved": 0.0}


def test_bands_average_over_tasks_not_over_runs():
    """A task with more replicates must not weigh more inside its band."""
    from eval.baseline import bands_of

    data = rows({"a": [True], "b": [False] * 9})
    out = bands_of(data, {"a": 1, "b": 1})
    assert out["one-liner"]["resolved"] == 0.5


def _task(name):
    return Task(name=name, prompt="", files={}, hidden="", why="")


def _recording_once(bundles, manifest_model, spent):
    """A stand-in for a paid run that records what it was asked to do."""
    def once(task, arm, model, root, effort="", budget=0.0):
        spent.append((task.name, effort, budget))
        bundle = Path(bundles) / f"{task.name}-{len(spent)}"
        bundle.mkdir(parents=True)
        (bundle / "manifest.json").write_text(json.dumps({"model": manifest_model}),
                                              encoding="utf-8")
        return Run(task=task.name, arm=arm, claimed=True, resolved=True,
                   outcome="resolved", bundle=str(bundle))
    return once


def test_a_sweep_stops_the_moment_a_bundle_names_another_model(tmp_path, monkeypatch):
    """Adversarial. E4 was an arm labelled present and running absent; a model
    pin that only warns is the same defect one field over, and an unattended
    sweep is where it would buy a whole night of the wrong model."""
    spent: list = []
    monkeypatch.setattr("eval.baseline.once",
                        _recording_once(tmp_path / "b", "claude-haiku-4-5-20251001", spent))
    journal = tmp_path / "j.jsonl"

    with pytest.raises(SystemExit):
        run_baseline([_task("a"), _task("b")], "vanilla", "claude-sonnet-5", 3,
                     tmp_path / "b", 0, journal, expect="claude-sonnet-5")

    assert len(spent) == 1, "it kept paying after the mismatch"
    assert len(read_journal(journal)) == 1, "the run it did pay for was thrown away"


def test_a_sweep_on_the_model_it_asked_for_runs_every_replicate(tmp_path, monkeypatch):
    """The forward direction. A guard that fires on the right model stops
    everything, and only this test tells that apart from a working one."""
    spent: list = []
    monkeypatch.setattr("eval.baseline.once",
                        _recording_once(tmp_path / "b", "claude-sonnet-5", spent))

    rows = run_baseline([_task("a"), _task("b")], "vanilla", "claude-sonnet-5", 3,
                        tmp_path / "b", 0, tmp_path / "j.jsonl", effort="high",
                        budget=6.0, expect="claude-sonnet-5")

    assert len(rows) == 6
    assert {(effort, budget) for _, effort, budget in spent} == {("high", 6.0)}


def test_a_restart_repeats_nothing_it_already_paid_for(tmp_path, monkeypatch):
    spent: list = []
    monkeypatch.setattr("eval.baseline.once",
                        _recording_once(tmp_path / "b", "m", spent))
    journal = tmp_path / "j.jsonl"

    run_baseline([_task("a")], "vanilla", "m", 3, tmp_path / "b", 0, journal)
    assert len(spent) == 3
    rows = run_baseline([_task("a"), _task("b")], "vanilla", "m", 3, tmp_path / "b",
                        0, journal)

    assert len(spent) == 6, "it bought task a a second time"
    assert len(rows) == 6


def test_a_restart_finishes_a_task_that_died_between_replicates(tmp_path, monkeypatch):
    """Resume by task name alone would skip the two replicates still owed."""
    spent: list = []
    monkeypatch.setattr("eval.baseline.once",
                        _recording_once(tmp_path / "b", "m", spent))
    journal = tmp_path / "j.jsonl"
    journal.write_text(json.dumps({"task": "a", "resolved": True}) + "\n",
                       encoding="utf-8")

    run_baseline([_task("a")], "vanilla", "m", 3, tmp_path / "b", 0, journal)

    assert len(spent) == 2
