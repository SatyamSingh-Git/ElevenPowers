"""Repository selection must preserve real inputs and exclude generated noise."""
import subprocess

from core.evidence import source_files


def git(root, *args):
    return subprocess.run(["git", "-c", f"safe.directory={root.as_posix()}", *args],
                          cwd=root, check=True, capture_output=True)


def test_git_ignores_generated_data_but_keeps_tracked_and_new_source(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / ".gitignore").write_text("generated/\ntracked.json\n")
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated/noise.json").write_text("{}")
    (tmp_path / "tracked.json").write_text("{}")
    git(tmp_path, "add", "-f", "tracked.json")
    (tmp_path / "new.py").write_text("x = 1")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github/ci.yml").write_text("name: ci")
    assert source_files(tmp_path) == [".github/ci.yml", "new.py", "tracked.json"]


def test_git_scan_stays_in_selected_root(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "outer.py").write_text("x = 1")
    child = tmp_path / "child"
    child.mkdir()
    (child / "inner.py").write_text("x = 2")
    assert source_files(child) == ["inner.py"]


def test_git_scan_does_not_enter_nested_repository(tmp_path):
    git(tmp_path, "init", "-q")
    nested = tmp_path / "nested"
    nested.mkdir()
    git(nested, "init", "-q")
    (nested / "private.py").write_text("x = 1")
    (tmp_path / "own.py").write_text("x = 2")
    assert source_files(tmp_path) == ["own.py"]
