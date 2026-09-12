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
