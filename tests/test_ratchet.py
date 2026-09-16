"""Keeping the best proven state, and refusing to offer an unsuitable one.

PLAN §5.6: *a long attempt ends at its latest patch, not its best.* Measured
elsewhere, 60-69% of coding-agent failures reach and edit the correct functions
and then produce a wrong patch.

Both directions, per §5.0:

    forward       a task that proved a state and then moved off it is offered
                  the proven one back
    adversarial   nothing is offered when nothing was proven, when the tree has
                  not moved, or when HEAD has

A module that offered on every stop would pass the forward test alone; one that
never offered would pass the adversarial tests alone. Neither is the feature.

Real `git init` throughout: the whole mechanism is `commit-tree` against a
temporary index and a private ref, and a mocked git would test the mock.
"""

from __future__ import annotations

import subprocess

import pytest

from core import ratchet


def git(root, *args):
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, f"git {' '.join(args)}: {done.stderr}"
    return done.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "probe@example.invalid")
    git(tmp_path, "config", "user.name", "probe")
    (tmp_path / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def test_a_proven_state_is_offered_back_after_the_tree_moves(repo):
    """Forward: the whole point."""
    (repo / "app.py").write_text("def add(a, b):\n    return a + b  # proven\n", encoding="utf-8")
    commit = ratchet.snapshot(repo, "t1", "declared checks green")
    assert commit

    (repo / "app.py").write_text("def add(a, b):\n    return None  # broken it\n", encoding="utf-8")
    said = ratchet.offer(repo, "t1")
    assert "declared checks passed" in said
    assert commit[:10] in said
    assert "git restore" in said


def test_untracked_work_is_kept_too(repo):
    """The test an agent just wrote is untracked, and is the thing worth keeping."""
    (repo / "test_new.py").write_text("def test_x():\n    assert True\n", encoding="utf-8")
    commit = ratchet.snapshot(repo, "t1", "green")
    listing = git(repo, "ls-tree", "-r", "--name-only", commit)
    assert "test_new.py" in listing


def test_nothing_is_offered_when_nothing_was_proven(repo):
    """Adversarial: silence, not a hedge."""
    (repo / "app.py").write_text("def add(a, b):\n    return None\n", encoding="utf-8")
    assert ratchet.offer(repo, "never-proved-anything") == ""


def test_nothing_is_offered_when_the_tree_has_not_moved(repo):
    """Adversarial: offering the tree the user is already looking at is noise."""
    (repo / "app.py").write_text("def add(a, b):\n    return a + b  # proven\n", encoding="utf-8")
    ratchet.snapshot(repo, "t1", "green")
    assert ratchet.offer(repo, "t1") == ""


def test_a_moved_head_makes_the_snapshot_ineligible(repo):
    """Cline's compare-and-swap condition, and the trap the 2026 work named.

    Restoring would undo whatever moved HEAD. The bytes would come back
    perfectly and the result would be wrong, which is exactly the failure task
    success cannot see — so eligibility is asserted separately from outcome.
    """
    (repo / "app.py").write_text("def add(a, b):\n    return a + b  # proven\n", encoding="utf-8")
    commit = ratchet.snapshot(repo, "t1", "green")
    assert ratchet.eligible(repo, commit)

    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "the agent committed its own work")
    (repo / "app.py").write_text("def add(a, b):\n    return None\n", encoding="utf-8")

    assert not ratchet.eligible(repo, commit)
    said = ratchet.offer(repo, "t1")
    assert "HEAD has moved" in said
    assert "git restore" not in said, "an ineligible snapshot must not be offered as one"


def test_the_working_tree_index_and_branches_are_untouched(repo):
    """A runtime that changes what it observes is the defect, not the feature."""
    (repo / "app.py").write_text("def add(a, b):\n    return a + b  # proven\n", encoding="utf-8")
    before = (repo / "app.py").read_text(encoding="utf-8")
    head = git(repo, "rev-parse", "HEAD")
    staged = git(repo, "diff", "--cached", "--name-only")

    ratchet.snapshot(repo, "t1", "green")

    assert (repo / "app.py").read_text(encoding="utf-8") == before
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "diff", "--cached", "--name-only") == staged, "it staged the agent's work"
    assert git(repo, "branch", "--list") == "" or "elevenpowers" not in git(repo, "branch", "--list")
    assert "elevenpowers" not in git(repo, "tag", "--list")
    assert git(repo, "stash", "list") == "", "it used the user's stash"


def test_outside_a_repository_it_simply_does_nothing(tmp_path):
    assert ratchet.snapshot(tmp_path, "t1", "green") is None
    assert ratchet.offer(tmp_path, "t1") == ""
