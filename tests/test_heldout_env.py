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
