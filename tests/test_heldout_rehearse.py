"""Each held-out task is rehearsed on its own gold patch before any paid run."""
from tests.test_heldout_grading import _task


def test_a_sound_task_rehearses_clean_and_calibrates_vacuity_both_ways(tmp_path):
    from eval.heldout_rehearse import rehearse
    task, _ = _task(tmp_path)
    task.source["import_names"] = ["pkg"]
    value = rehearse(task, tmp_path / "work")
    assert (value["canary"], value["base_fails"], value["gold_resolves"]) == (True, True, True)
    # With its own tests the revert is caught; without them the old suite cannot tell.
    assert (value["gold_vacuous"], value["source_vacuous"]) == (False, True)
    assert value["usable"] is True


def test_an_importable_answer_makes_the_task_unusable(tmp_path):
    from eval.heldout_rehearse import rehearse
    task, _ = _task(tmp_path)
    task.source["import_names"] = ["json"]
    value = rehearse(task, tmp_path / "work")
    assert value["canary"] is False and value["usable"] is False


def test_a_probe_that_calls_the_full_gold_vacuous_makes_the_task_unusable(tmp_path, monkeypatch):
    from eval import heldout_rehearse as r
    task, _ = _task(tmp_path)
    task.source["import_names"] = ["pkg"]
    monkeypatch.setattr(r, "vacuity", lambda *a, **k: {"vacuous": True, "reason": "revert survived"})
    value = r.rehearse(task, tmp_path / "work")
    assert value["gold_vacuous"] is True and value["usable"] is False


def test_a_task_comes_from_its_corpus_with_its_repository_test_directory():
    from eval.heldout_run import load_task
    corpus = {"tasks": [{"name": "t", "prompt": "p", "url": "u", "python": "py"}],
              "environments": {"u": {"test_dir": "testing/"}}}
    task = load_task(corpus, "t")
    assert (task.name, task.prompt, task.source["test_dir"], task.source["python"]) == ("t", "p", "testing", "py")


def test_a_probe_that_kills_the_source_only_gold_makes_the_task_unusable(tmp_path, monkeypatch):
    from eval import heldout_rehearse as r
    task, _ = _task(tmp_path)
    task.source["import_names"] = ["pkg"]
    # Validation leaves the base suite green, so reverting the source alone must survive.
    monkeypatch.setattr(r, "vacuity", lambda *a, **k: {"vacuous": False, "reason": "revert killed"})
    value = r.rehearse(task, tmp_path / "work")
    assert value["source_vacuous"] is False and value["usable"] is False
