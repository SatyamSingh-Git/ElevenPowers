"""Real-task grading honours a task's own interpreter and test directory."""
import subprocess
import sys

from eval.task import Task


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def _task(tmp_path):
    repo = tmp_path / "upstream"
    (repo / "pkg").mkdir(parents=True)
    (repo / "test").mkdir()
    _git(tmp_path, "init", "-q", str(repo))
    (repo / "pkg" / "__init__.py").write_text("", encoding="utf8")
    (repo / "pkg" / "mod.py").write_text("def value():\n    return 1\n", encoding="utf8")
    (repo / "test" / "test_old.py").write_text("from pkg.mod import value\n\n\ndef test_old():\n    assert value() > 0\n", encoding="utf8")
    # Outside the suite and not importable here: collecting from the root would abort on it.
    (repo / "benchmarks").mkdir()
    (repo / "benchmarks" / "test_speed.py").write_text("import not_installed_anywhere\n", encoding="utf8")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD").strip()
    (repo / "pkg" / "mod.py").write_text("def value():\n    return 2\n", encoding="utf8")
    hidden = "from pkg.mod import value\n\n\ndef test_new():\n    assert value() == 2\n"
    (repo / "test" / "test_new.py").write_text(hidden, encoding="utf8")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "fix")
    fix = _git(repo, "rev-parse", "HEAD").strip()
    gold = _git(repo, "diff", base, fix, "--", "pkg")
    source = {"repo": str(repo), "base": base, "fix": fix, "hidden_files": {"test/test_new.py": hidden},
              "f2p": ["test/test_new.py::test_new"], "p2p": ["test/test_old.py::test_old"],
              "env": {"PYTHONPATH": "."}, "python": sys.executable, "test_dir": "test"}
    return Task(name="t", prompt="", files={}, hidden="", why="", source=source), gold


def test_a_gold_patch_resolves_under_the_task_test_directory(tmp_path):
    from eval.live import grade_patch
    task, gold = _task(tmp_path)
    assert grade_patch(task, gold, tmp_path / "work").outcome == "resolved"


def test_an_empty_patch_is_unfixed_not_a_setup_failure(tmp_path):
    from eval.live import grade_patch
    task, _ = _task(tmp_path)
    assert grade_patch(task, "", tmp_path / "work").outcome == "unfixed"


def test_the_task_interpreter_is_the_one_that_runs_the_suite(tmp_path):
    import pytest
    from eval.live import grade_patch
    task, gold = _task(tmp_path)
    task.source["python"] = str(tmp_path / "no-such-python")
    with pytest.raises(FileNotFoundError):
        grade_patch(task, gold, tmp_path / "work")
