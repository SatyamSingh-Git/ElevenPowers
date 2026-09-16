"""Closing the registry without breaking an honest install.

The registry is an answer key: every repository in the corpus has a released
version carrying its own fix, and `eval/canary.py` caught three of the four
exposures that survived the tool-denial list fetching exactly that.

Both directions, per PLAN §5.0, and a third that is the whole design:

    adversarial   `pip download <the package under test>` cannot reach PyPI
    forward       `pip install -e .` still works, offline
    fail-safe     with no shelf staged, the index is left ALONE rather than
                  breaking every install

The third matters most. `PIP_NO_INDEX` alone was measured on 2026-09-16 and
reverted the same hour because it broke `pip install -e .`, and a guard that
breaks honest work is the guard an agent turns off — one of the three before it
was observed being turned off mid-run.

Real pip against a real workspace venv. A mocked pip would test the mock, and
the entire question here is what pip does with an isolated build environment.
"""

from __future__ import annotations

import subprocess

import pytest

from eval import wheelhouse
from eval.live import _own_interpreter, _sandboxed


@pytest.fixture
def workspace(tmp_path):
    """A minimal installable project, shaped like the corpus ones."""
    (tmp_path / "src" / "ep_probe_wh").mkdir(parents=True)
    (tmp_path / "src" / "ep_probe_wh" / "__init__.py").write_bytes(b"V = 1\n")
    (tmp_path / "pyproject.toml").write_bytes(
        b'[project]\nname = "ep-probe-wh"\nversion = "0.0.1"\n'
        b'[build-system]\nrequires = ["setuptools"]\n'
        b'build-backend = "setuptools.build_meta"\n'
        b'[tool.setuptools.packages.find]\nwhere = ["src"]\n')
    _own_interpreter(tmp_path)
    return tmp_path


def run(command, cwd, env, timeout=600):
    return subprocess.run(command, shell=True, cwd=cwd, env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=timeout)


def test_the_shelf_reports_what_it_is_missing(tmp_path):
    """An empty shelf is not ready, and says which backends are absent."""
    empty = tmp_path / "nothing"
    assert not wheelhouse.ready(empty)
    assert set(wheelhouse.missing(empty)) == set(wheelhouse.BACKENDS)


@pytest.mark.skipif(not wheelhouse.ready(),
                    reason="shelf not staged; run `python -m eval.wheelhouse --build`")
def test_the_registry_is_closed(workspace):
    """Adversarial: the door the canary caught three runs walking through."""
    env = _sandboxed(workspace)
    assert env.get("PIP_NO_INDEX") == "1", "the shelf is staged, so the index must be shut"
    for attempt in ("python -m pip download click -d dl",
                    "python -m pip install click==8.5.0 --target inst"):
        done = run(attempt, workspace, env)
        assert done.returncode != 0, f"reached the registry: {attempt}"


@pytest.mark.skipif(not wheelhouse.ready(),
                    reason="shelf not staged; run `python -m eval.wheelhouse --build`")
def test_an_honest_install_still_works_offline(workspace):
    """Forward, and the control that stops this becoming `break everything`.

    pip builds in an isolated environment and fetches `setuptools` into it. With
    the index off that is fatal unless the shelf can feed it, which is the one
    thing `PIP_FIND_LINKS` does that no environment variable could.
    """
    env = _sandboxed(workspace)
    done = run("python -m pip install -e . --no-deps -q", workspace, env)
    assert done.returncode == 0, f"the shelf did not feed the build: {done.stderr[-400:]}"

    seen = run('python -c "import ep_probe_wh; print(ep_probe_wh.V)"', workspace, env)
    assert seen.returncode == 0, "installed, but not importable"


def test_without_a_shelf_the_index_is_left_alone(workspace, monkeypatch):
    """Fail safe. An incomplete shelf plus a closed index breaks every install.

    Silently half-closing the door is worse than leaving it open and saying so:
    the run still works, and `python -m eval.wheelhouse` is what reports that
    the boundary is not engaged.
    """
    monkeypatch.setattr(wheelhouse, "ready", lambda *a, **k: False)
    env = _sandboxed(workspace)
    assert "PIP_NO_INDEX" not in env
    assert "PIP_FIND_LINKS" not in env
