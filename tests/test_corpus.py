"""The corpus has to be the same corpus on the next machine and the next week.

A benchmark rebuilt by re-scanning "the last 150 commits" is a different
benchmark every time the upstream repositories gain commits, and it would carry
the same name and a different score. So the pins are tested here, in both
directions: the lock must identify a corpus, and a rebuild must refuse rather
than substitute when a pinned commit cannot be reached.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from eval.corpus import BANDS, band, lock, rebuild


@pytest.fixture
def upstream(tmp_path):
    """A repository with one fixable bug, mined the way a real one would be."""
    repo = tmp_path / "src-repo"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()
    for rel, body in ((".gitignore", "__pycache__/\n"), ("src/__init__.py", ""),
                      ("src/app.py", "def double(n):\n    return n\n"),
                      ("tests/__init__.py", ""),
                      ("tests/test_keep.py",
                       "from src.app import double\n\n\ndef test_zero():\n"
                       "    assert double(0) == 0\n")):
        (repo / rel).write_text(body, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True, capture_output=True)
    _commit(repo, "before")
    (repo / "src/app.py").write_text("def double(n):\n    return n * 2\n", encoding="utf-8")
    (repo / "tests/test_new.py").write_text(
        "from src.app import double\n\n\ndef test_double():\n    assert double(2) == 4\n",
        encoding="utf-8")
    fix = _commit(repo, "double() returned its argument")
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin",
                    "https://example.invalid/src-repo.git"], check=True, capture_output=True)
    return repo, fix


def _commit(repo: Path, message: str) -> str:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=A", "-c",
                    "user.email=a@example.invalid", "commit", "-qm", message],
                   check=True, capture_output=True)
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()


def test_bands_label_by_the_size_of_the_maintainers_change():
    assert band(1) == "one-liner"
    assert band(3) == "one-liner"
    assert band(4) == "small"
    assert band(20) == "small"
    assert band(21) == "substantial"
    assert band(0) == "empty"
    # Every band is reachable, or one of them is decoration.
    assert {band(n) for n in (1, 10, 100)} == {name for name, _, _ in BANDS}


def test_the_lock_identifies_a_corpus_without_carrying_it(tmp_path):
    """3.8KB of pins rather than 1.8MB of test bodies, and no loss of identity."""
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([{
        "name": "thing-abc", "origin": "https://example.invalid/thing.git",
        "base": "b" * 40, "fix": "f" * 40,
        "hidden_files": {"tests/test_a.py": "x" * 50_000},
        "f2p": ["tests/test_a.py::test_one"], "p2p": ["tests/test_a.py::test_two"],
    }]), encoding="utf-8")

    out = tmp_path / "corpus.lock"
    assert lock(corpus, out) == 0
    pinned = json.loads(out.read_text(encoding="utf-8"))
    assert pinned[0]["fix"] == "f" * 40
    assert pinned[0]["tests"] == ["tests/test_a.py"]
    assert out.stat().st_size < corpus.stat().st_size / 10


def test_an_instance_without_an_origin_is_reported_as_unpinnable(tmp_path):
    """It would rebuild only on the disk that mined it, which is not a pin."""
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([{
        "name": "local-only", "origin": "", "base": "b" * 40, "fix": "f" * 40,
        "hidden_files": {"tests/test_a.py": "x"}, "f2p": [], "p2p": [],
    }]), encoding="utf-8")
    assert lock(corpus, tmp_path / "corpus.lock") == 1


def test_a_rebuild_reproduces_the_pinned_instance(upstream, tmp_path):
    """The forward direction: the pins are enough to get the corpus back."""
    repo, fix = upstream
    lockfile = tmp_path / "corpus.lock"
    lockfile.write_text(json.dumps([{
        "name": "src-repo", "origin": "https://example.invalid/src-repo.git",
        "base": "", "fix": fix, "tests": ["tests/test_new.py"],
    }]), encoding="utf-8")

    out = tmp_path / "rebuilt.json"
    assert rebuild(lockfile, repo.parent, {"PYTHONPATH": "src"}, out) == 0
    rows = json.loads(out.read_text(encoding="utf-8"))
    assert [r["f2p"] for r in rows] == [["tests/test_new.py::test_double"]]
    assert rows[0]["p2p"] == ["tests/test_keep.py::test_zero"]


def test_a_rebuild_refuses_rather_than_substituting(upstream, tmp_path):
    """The adversarial direction, and the one that matters.

    A rebuild that quietly mined a nearby commit would produce a corpus that
    looks like the original and scores differently, which is worse than no
    rebuild at all. An unreachable pin has to come back missing.
    """
    repo, _ = upstream
    lockfile = tmp_path / "corpus.lock"
    lockfile.write_text(json.dumps([{
        "name": "src-repo", "origin": "https://example.invalid/src-repo.git",
        "base": "", "fix": "0" * 40, "tests": ["tests/test_new.py"],
    }]), encoding="utf-8")

    out = tmp_path / "rebuilt.json"
    assert rebuild(lockfile, repo.parent, {"PYTHONPATH": "src"}, out) == 1
    assert json.loads(out.read_text(encoding="utf-8")) == []


def test_a_node_id_carrying_an_installed_version_is_refused():
    """A pinned identifier holding a value from the machine is not pinned.

    Four click tasks pinned `test_attr_deprecated[click-__version__-8.4.2.dev0]`
    into their preservation sets. That version is click's at none of those
    commits: it is setuptools-scm's fallback inside a tree with no git history,
    which is what a stray editable install saw. Install click properly and the
    node is renamed, so a preserved test appears to have vanished and the
    maintainer's own fix grades as a regression.
    """
    import importlib.metadata

    from eval.mine import machine_dependent

    version = importlib.metadata.version("pytest")
    node = f"tests/test_deprecations.py::test_attr_deprecated[pytest-__version__-{version}]"

    assert machine_dependent([node]) == [node]


def test_a_machine_dependent_node_is_dropped_not_the_whole_instance(upstream, tmp_path):
    """Refusing the instance would have deleted a repository from the corpus.

    The offending node passes at every click commit, so it is in every click
    task's preservation set: rejecting on it removes all of click rather than
    one observation out of eighteen hundred. It is dropped and recorded instead,
    because a preservation set that quietly shrank would be its own defect.
    """
    import importlib.metadata

    from eval.mine import machine_dependent

    version = importlib.metadata.version("pytest")
    unstable = f"tests/t.py::test_attr[pytest-__version__-{version}]"
    p2p = ["tests/test_keep.py::test_label", unstable]

    dropped = machine_dependent(p2p)
    assert dropped == [unstable]
    assert [n for n in p2p if n not in set(dropped)] == ["tests/test_keep.py::test_label"]


def test_an_ordinary_parameter_that_looks_like_a_version_is_kept():
    """The forward direction. A rule that refuses every parametrised node would
    empty the preservation sets, and a corpus with nothing to preserve cannot
    tell a fix from a patch that also broke something -- which is the defect the
    preservation set exists to catch. Both halves are required, the
    distribution's name and its version, and only this says so.
    """
    from eval.mine import machine_dependent

    assert machine_dependent([
        "tests/test_compat.py::test_strip_ansi[IP-192.1.0.2]",
        "tests/test_basic.py::test_group",
        "tests/test_versions.py::test_parse[1.2.3-expected]",
    ]) == []


def _instance(name, lines):
    return {"name": name, "origin": "u", "base": "b", "fix": "f", "gold_lines": lines,
            "f2p": ["t::f"], "p2p": ["t::keep"], "hidden_files": {}, "env": {},
            "changed": [], "prompt": ""}


def test_a_band_selected_corpus_says_so_every_time_it_is_shown(tmp_path, capsys):
    """A benchmark that quietly excluded half its tasks by difficulty would be
    E6 wearing a different hat, even though gold-patch size is fixed upstream
    and cannot favour an arm. The line that used to print here asserted the
    opposite -- "nothing was dropped for being easy or hard" -- and would have
    gone on asserting it over a corpus with forty-five tasks removed.
    """
    from eval.corpus import show

    selected = tmp_path / "selected.json"
    selected.write_text(json.dumps(
        [_instance("a", 2), _instance("b", 40)]), encoding="utf-8")

    show(selected)

    printed = capsys.readouterr().out
    assert "no small task(s)" in printed
    assert "Nothing was dropped" not in printed


def test_an_unselected_corpus_does_not_claim_a_selection(tmp_path, capsys):
    """The forward direction. A notice that fires on every corpus says nothing,
    and would make the real one invisible.
    """
    from eval.corpus import show

    everything = tmp_path / "all.json"
    everything.write_text(json.dumps(
        [_instance("a", 2), _instance("b", 10), _instance("c", 40)]), encoding="utf-8")

    show(everything)

    printed = capsys.readouterr().out
    assert "Nothing was dropped" in printed
    assert "Selected:" not in printed
