"""The audit's remaining findings: recovery, profiles, caching and delivery.

`docs/research/audit_2026_09_19/`, findings F2, F3, F6, F8, F9, F10, F12. The
evidence-integrity half is in `test_audit_20260919.py`; these are the ones about
a checkpoint you cannot get back, a profile doing work it says it does not, an
answer cached past the inputs it was computed from, and a note nobody receives.
"""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys

import pytest

from core import radius, ratchet, stress
from core.config import Config
from core.evidence import Evidence, Kind, Result, source_files, tree_hash
from core.ledger import Ledger
from core.obligations import Claim


def git(root, *args):
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, f"git {' '.join(args)}: {done.stderr}"
    return done.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "probe@example.invalid")
    git(tmp_path, "config", "user.name", "probe")
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(
        "def test_a():\n    assert True\n", encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def passing_suite(root):
    observed = source_files(root)
    return Evidence(Kind.SUITE, "pytest tests", Result.PASS, observed,
                    tree_hash(root, observed), passed=1, counted=True, scope="source")


# --- F2: permission to end a turn is not proof of a tree --------------------

def test_a_clarifying_question_does_not_create_a_checkpoint(repo, monkeypatch):
    """`settle` returns VERIFIED for a question so the turn may end without any
    claim being discharged, and `on_stop` read that as proof of a candidate.

    The audit ended a turn with a question on an UNVERIFIED claim carrying zero
    evidence and got a checkpoint noted "the declared checks passed here".
    """
    from core import hook

    led = Ledger(root=repo, task="q", base=git(repo, "rev-parse", "HEAD"),
                 request="refactor the function", claims=[Claim.REFACTOR_SAFE],
                 _config=Config(profile="guide"))
    monkeypatch.setattr(Ledger, "load", classmethod(lambda cls, root: led))
    monkeypatch.setattr(Ledger, "save", lambda self: None)
    hook.on_stop({"last_assistant_message": "Which behaviour do you want?"}, repo)
    assert led.evidence == []
    assert not ratchet.proven(repo, "q")


# --- F9: `off` records; it does not run things ------------------------------

def _stopped_under(repo, monkeypatch, profile):
    from core import hook

    calls = []
    led = Ledger(root=repo, task=profile, base=git(repo, "rev-parse", "HEAD"),
                 request="refactor", claims=[Claim.REFACTOR_SAFE],
                 evidence=[passing_suite(repo)],
                 _config=Config(profile=profile, commands={"tests": "pytest tests"}))
    monkeypatch.setattr(Ledger, "load", classmethod(lambda cls, root: led))
    monkeypatch.setattr(Ledger, "save", lambda self: None)
    monkeypatch.setattr(stress, "on_the_old_tree",
                        lambda *a, **k: (calls.append(a), (True, "1 passed"))[1])
    with contextlib.redirect_stdout(io.StringIO()):
        hook.on_stop({"last_assistant_message": "Done."}, repo)
    return calls


def test_the_off_profile_runs_no_checks_of_its_own(repo, monkeypatch):
    """`off` is documented as *record evidence, say nothing, never block*.

    It was building a git worktree and running the declared suite inside it
    before going quiet - real work, real seconds, on the profile chosen by
    someone who asked for none.
    """
    assert _stopped_under(repo, monkeypatch, "off") == []


def test_guide_still_runs_its_checks(repo, monkeypatch):
    """Forward, and the one that matters: the capability is off for `off` only."""
    assert _stopped_under(repo, monkeypatch, "guide")


# --- F3: a cached answer is valid only while its inputs are -----------------

def test_editing_a_carried_test_invalidates_the_cached_verdict(repo, monkeypatch):
    """The base commit does not move. The tests carried onto it do.

    Written against `stress.stress` and not against `_inputs_stamp`: the first
    version of this test asserted the fingerprint changed, which it did whether
    or not anything consulted it. Flipping the cache condition left it green,
    so it was measuring a helper rather than the behaviour.
    """
    runs = []
    monkeypatch.setattr(stress, "on_the_old_tree",
                        lambda *a, **k: (runs.append(a), (True, "1 passed"))[1])
    led = Ledger(root=repo, task="t", base=git(repo, "rev-parse", "HEAD"),
                 touched=["tests/test_a.py"], evidence=[passing_suite(repo)],
                 _config=Config(commands={"tests": "pytest tests"}))

    led.discrimination, led.failed_before = stress.stress(led)
    assert len(runs) == 1

    led.discrimination, led.failed_before = stress.stress(led)
    assert len(runs) == 1, "an unchanged input must reuse the cached answer"

    (repo / "tests" / "test_a.py").write_text(
        "from app import value\ndef test_a():\n    assert value == 2\n", encoding="utf-8")
    led.discrimination, led.failed_before = stress.stress(led)
    assert len(runs) == 2, "the carried test changed and the answer was reused anyway"


def test_a_failed_invocation_does_not_spend_the_confirmation_attempt(repo):
    """The CONFIRMED note suppresses any later try, and it was written before
    the result was inspected - so a usage error permanently prevented the run
    that would have answered the question."""
    led = Ledger(root=repo, task="t", base=git(repo, "rev-parse", "HEAD"),
                 failed_before=["tests/test_a.py::test_a"],
                 _config=Config(commands={
                     "tests": f"{sys.executable} -m pytest --not-a-real-flag tests"}))
    stress.confirm(led)
    assert not any(d.get("what") == stress.CONFIRMED for d in led.decisions)


# --- F6: context delivery is tracked apart from file observation ------------

def test_reading_a_file_does_not_suppress_its_first_edit_brief(repo, monkeypatch):
    """The brief was gated on `seen`, which records reads. An agent reads
    before it edits essentially always, so the note meant for the first edit
    was suppressed by the read that preceded it - every time."""
    from core import hook

    (repo / "app.py").write_text("class Thing:\n    pass\n", encoding="utf-8")
    (repo / "uses.py").write_text("from app import Thing\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "with a user")

    led = Ledger(root=repo, task="t")
    monkeypatch.setattr(Ledger, "load", classmethod(lambda cls, root: led))
    monkeypatch.setattr(Ledger, "save", lambda self: None)
    edit = {"tool_name": "Edit", "tool_input": {"file_path": str(repo / "app.py")}}

    hook.on_post_tool({"tool_name": "Read",
                       "tool_input": {"file_path": str(repo / "app.py")}}, repo)
    said = io.StringIO()
    with contextlib.redirect_stdout(said):
        hook.on_pre_tool(edit, repo)
    assert said.getvalue().strip(), "the read consumed the brief meant for the edit"

    again = io.StringIO()
    with contextlib.redirect_stdout(again):
        hook.on_pre_tool(edit, repo)
    assert not again.getvalue().strip(), "repeated edits spam the same note"


# --- F8: the offered recovery has to produce the checkpoint -----------------

def test_the_offer_does_not_recommend_a_restore_that_would_not_restore(repo):
    """`git restore` rewrites tracked paths and leaves everything added since.

    The audit followed the printed instruction in a real repository and the
    failing test it had just written survived it, with the tree still differing
    afterwards - so the command did not do the thing it was offered for.
    """
    commit = ratchet.snapshot(repo, "t", "probe snapshot")
    assert commit
    (repo / "tests" / "test_later.py").write_text(
        "def test_later():\n    assert False\n", encoding="utf-8")
    said = ratchet.offer(repo, "t")
    assert "git worktree add" in said, said
    assert "would NOT reproduce it" in said, said
    assert "test_later.py" in said, said
    assert ratchet.added_since(repo, commit) == ["tests/test_later.py"]


def test_an_in_place_restore_is_offered_when_it_is_faithful(repo):
    """Forward: with nothing added since, the simple command is correct and is
    still the one offered. A fix that only ever refuses is not a fix."""
    ratchet.snapshot(repo, "t", "probe snapshot")
    (repo / "app.py").write_text("value = 99\n", encoding="utf-8")
    said = ratchet.offer(repo, "t")
    assert "git restore --source=" in said, said
    assert "would NOT reproduce it" not in said, said


# --- F10 and F12 ------------------------------------------------------------

def test_an_unchanged_tracked_file_has_no_changed_lines(repo):
    """An empty diff was read as "untracked", so a file opened and reverted came
    back as wholly changed."""
    base = git(repo, "rev-parse", "HEAD")
    assert radius.changed_lines(repo, base, "app.py") == set()


def test_a_genuinely_new_file_still_reports_its_lines(repo):
    """Forward: the untracked case is what that branch exists for."""
    base = git(repo, "rev-parse", "HEAD")
    (repo / "fresh.py").write_text("a = 1\nb = 2\n", encoding="utf-8")
    assert radius.changed_lines(repo, base, "fresh.py") == {1, 2}


def test_pooling_keeps_every_attempt_at_a_repeated_task():
    """One success and one failure in different sweeps is two attempts and a
    50% random pick - not one attempt and zero coverage.

    The same dict-comprehension overwrite that once laundered a failing monorepo
    package into a passing record, in the reporting layer this time.
    """
    from eval.pool import measure, pools

    rows = [("first", "task", "vanilla", "resolved", 1),
            ("second", "task", "vanilla", "unfixed", 2)]
    got = measure(pools(rows), None, "vanilla")
    assert got["attempts"] == 2, got
    assert got["coverage"] == 1.0, got
    assert got["random_pick"] == 0.5, got      # a fraction, as pool.py reports it


def test_pooling_a_single_sweep_is_unchanged(repo):
    """Forward: the per-sweep numbers the findings quote must not move."""
    from eval.pool import measure, pools

    rows = [("first", "a", "vanilla", "resolved", 1),
            ("first", "b", "vanilla", "unfixed", 2)]
    got = measure(pools(rows), "first", "vanilla")
    assert got["attempts"] == 2 and got["tasks"] == 2
    assert got["coverage"] == 0.5
