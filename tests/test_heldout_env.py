"""Closed-book environments: test dependencies installed, the package itself not importable."""
import sys

import pytest


def _write(root, files):
    for name, body in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf8")
    return root


@pytest.mark.parametrize("files, expected", [
    ({"src/pkg/__init__.py": "", "tests/test_a.py": ""}, {"source_dir": "src/", "test_dir": "tests/", "pythonpath": "src"}),
    ({"pkg/__init__.py": "", "tests/test_a.py": ""}, {"source_dir": "pkg/", "test_dir": "tests/", "pythonpath": "."}),
    ({"pkg/__init__.py": "", "test/test_a.py": ""}, {"source_dir": "pkg/", "test_dir": "test/", "pythonpath": "."}),
    ({"single.py": "", "tests/test_a.py": ""}, {"source_dir": "single.py", "test_dir": "tests/", "pythonpath": "."}),
    ({"src/pkg/__init__.py": "", "pkg/notes.txt": "", "tests/test_a.py": ""},
     {"source_dir": "src/", "test_dir": "tests/", "pythonpath": "src"}),
])
def test_layout_is_discovered_per_repository(tmp_path, files, expected):
    from eval.heldout_env import layout
    assert layout(_write(tmp_path, files), import_names=["pkg" if "single.py" not in files else "single"]) == expected


def test_a_repository_without_tests_has_no_layout(tmp_path):
    from eval.heldout_env import layout
    assert layout(_write(tmp_path, {"pkg/__init__.py": ""}), import_names=["pkg"]) is None


PYPROJECT_GROUP = '[project]\nname = "pkg"\n[dependency-groups]\ntest = ["pytest", "hypothesis"]\n'
PYPROJECT_EXTRA = '[project]\nname = "pkg"\n[project.optional-dependencies]\nall = ["pytest"]\ntests = ["pytest", "freezegun"]\n'


@pytest.mark.parametrize("files, expected", [
    ({"pyproject.toml": PYPROJECT_GROUP}, [["install", ".", "--group", "test"]]),
    ({"pyproject.toml": PYPROJECT_EXTRA}, [["install", ".[tests]"]]),
    ({"pyproject.toml": '[project]\nname = "pkg"\n', "requirements-dev.txt": "pytest\n"},
     [["install", "."], ["install", "-r", "requirements-dev.txt"]]),
    ({"pyproject.toml": '[project]\nname = "pkg"\n'}, [["install", "."]]),
])
def test_install_follows_the_frozen_preference_order(tmp_path, files, expected):
    from eval.heldout_env import install_plan
    assert install_plan(_write(tmp_path, files)) == expected + [["install", "pytest"]]


def test_canary_fails_when_any_import_name_is_importable(tmp_path):
    from eval.heldout_env import canary
    assert canary(sys.executable, ["definitely_not_a_module_7d1f"], tmp_path)
    assert not canary(sys.executable, ["definitely_not_a_module_7d1f", "json"], tmp_path)


def test_the_installed_distribution_is_found_by_its_recorded_source(tmp_path):
    import json
    from eval.heldout_env import DISTRIBUTION, run
    repo = tmp_path / "repo"
    site = tmp_path / "site" / "my_dist-1.0.dist-info"
    site.mkdir(parents=True)
    repo.mkdir()
    (site / "METADATA").write_text("Metadata-Version: 2.1\nName: my-dist\nVersion: 1.0\n", encoding="utf8")
    (site / "direct_url.json").write_text(json.dumps({"url": repo.as_uri(), "dir_info": {}}), encoding="utf8")
    other = tmp_path / "site" / "a_other-1.0.dist-info"
    other.mkdir()
    (other / "METADATA").write_text("Metadata-Version: 2.1\nName: a-other\nVersion: 1.0\n", encoding="utf8")
    (other / "direct_url.json").write_text(json.dumps({"url": (tmp_path / "elsewhere").as_uri(), "dir_info": {}}),
                                           encoding="utf8")
    import os
    done = run([sys.executable, "-c", DISTRIBUTION, str(repo)], cwd=tmp_path, timeout=60, shell=False,
               env={**os.environ, "PYTHONPATH": str(tmp_path / "site")})
    assert done.stdout.strip() == "my-dist"


def _committed(root, files):
    import subprocess
    _write(root, files)
    for args in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "c"]):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
    return root


def test_the_package_must_import_from_its_own_tracked_source(tmp_path):
    from eval.heldout_env import importable
    good = _committed(tmp_path / "good", {"src/pkg/__init__.py": "VALUE = 1\n"})
    # The build (hatch-vcs, setuptools-scm) writes an ignored version module into the clone;
    # a task tree holds tracked files only, so the clone importing proves nothing.
    built = _committed(tmp_path / "built", {"src/pkg/__init__.py": "from ._version import version\n",
                                            ".gitignore": "src/pkg/_version.py\n"})
    _write(built, {"src/pkg/_version.py": "version = '1.0'\n"})
    assert importable(sys.executable, ["pkg"], good, "src")
    assert not importable(sys.executable, ["pkg"], built, "src")


@pytest.mark.parametrize("imports, expected", [
    (True, ("ready", "ready")),
    (False, ("rejected", "package does not import from its source tree")),
])
def test_a_repository_whose_source_cannot_import_is_rejected_once(tmp_path, monkeypatch, imports, expected):
    from types import SimpleNamespace
    from eval import heldout_env as e
    repo = _write(tmp_path / "repo", {"src/pkg/__init__.py": "", "tests/test_a.py": ""})
    monkeypatch.setattr(e, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout='["pkg"]', stderr=""))
    monkeypatch.setattr(e, "_distribution", lambda *a: "pkg")
    monkeypatch.setattr(e, "canary", lambda *a: True)
    monkeypatch.setattr(e, "importable", lambda *a: imports)
    value = e.build(repo, tmp_path / "venv")
    assert (value["state"], value["reason"]) == expected


def test_a_file_still_held_in_the_import_check_folder_does_not_end_the_check(tmp_path, monkeypatch):
    # Windows keeps a handle a moment after a child exits; a strict cleanup turned that into a crash.
    from eval import heldout_env as e
    good = _committed(tmp_path / "good", {"src/pkg/__init__.py": "VALUE = 1\n"})
    actual, held = e.run, []

    def holding(args, **kwargs):
        held.append(open(kwargs["cwd"] / "held.txt", "w"))
        return actual(args, **kwargs)

    monkeypatch.setattr(e, "run", holding)
    try:
        assert e.importable(sys.executable, ["pkg"], good, "src")
    finally:
        for handle in held:
            handle.close()


def test_a_file_still_held_in_the_canary_folder_does_not_end_the_build(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from eval import heldout_env as e
    repo = _write(tmp_path / "repo", {"src/pkg/__init__.py": "", "tests/test_a.py": ""})
    held = []

    def canary(python, names, cwd):
        held.append(open(e.Path(cwd) / "held.txt", "w"))
        return True

    monkeypatch.setattr(e, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout='["pkg"]', stderr=""))
    monkeypatch.setattr(e, "_distribution", lambda *a: "pkg")
    monkeypatch.setattr(e, "canary", canary)
    monkeypatch.setattr(e, "importable", lambda *a: True)
    try:
        assert e.build(repo, tmp_path / "venv")["state"] == "ready"
    finally:
        for handle in held:
            handle.close()
