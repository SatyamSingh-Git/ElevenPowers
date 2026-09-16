"""The reflexion between the documents and the code, and the ways it stays quiet.

Design: `docs/design/architecture-atlas.md` §8. A drift check that fires on
everything and one that fires on nothing are both indistinguishable from the
feature being absent, so the adversarial cases outnumber the forward ones.
"""

from __future__ import annotations

import pytest

from core import atlas

CORE = '''import os

from app.store import load


def run():
    return load()
'''

STORE = '''def load():
    return {}
'''

DOC = '''# Architecture

The runtime is `src/app/core.py`, which reads through `src/app/store.py`.
'''


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "src" / "app").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "app" / "core.py").write_text(CORE, encoding="utf-8")
    (tmp_path / "src" / "app" / "store.py").write_text(STORE, encoding="utf-8")
    (tmp_path / "tests" / "test_core.py").write_text(
        "def test_run():\n    assert True\n", encoding="utf-8")
    (tmp_path / "ARCHITECTURE.md").write_text(DOC, encoding="utf-8")
    return tmp_path


# --- forward ----------------------------------------------------------------

def test_a_module_no_document_names_is_divergent(repo):
    """The map went stale: the task added a module and nothing draws it."""
    (repo / "src" / "app" / "cache.py").write_text("def get():\n    return None\n",
                                                   encoding="utf-8")
    drift = atlas.reflexion(repo, added=["src/app/cache.py"], removed=[])

    assert drift
    assert drift.divergent == ("src/app/cache.py",)
    assert "ARCHITECTURE.md" in drift.documents


def test_a_document_naming_a_removed_path_is_absent(repo):
    """The doc went stale: the reference outlived the file.

    Tan, Wagner & Treude's mechanism — a reference surviving in documentation
    after the source is deleted.
    """
    (repo / "src" / "app" / "store.py").unlink()
    drift = atlas.reflexion(repo, added=[], removed=["src/app/store.py"])

    assert drift.absent == (("ARCHITECTURE.md", "src/app/store.py"),)


def test_naming_the_new_module_discharges_it(repo):
    """The forward control. Without this the check could be refusing everything."""
    (repo / "src" / "app" / "cache.py").write_text("def get():\n    return None\n",
                                                   encoding="utf-8")
    (repo / "ARCHITECTURE.md").write_text(
        DOC + "\nCaching lives in `src/app/cache.py`.\n", encoding="utf-8")
    drift = atlas.reflexion(repo, added=["src/app/cache.py"], removed=[])

    assert not drift, drift


# --- adversarial ------------------------------------------------------------

def test_a_repository_with_no_document_is_silent(repo):
    """Nothing to update if there is nothing to update.

    `core/surface.py`'s rule: an obligation nothing can discharge is a design
    error, not a finding.
    """
    (repo / "ARCHITECTURE.md").unlink()
    (repo / "src" / "app" / "cache.py").write_text("def get():\n    return None\n",
                                                   encoding="utf-8")
    drift = atlas.reflexion(repo, added=["src/app/cache.py"], removed=[])

    assert not drift
    assert drift.documents == ()


def test_standing_drift_is_counted_and_not_obligated(repo):
    """Undocumented modules this task did not add are a number, not a demand.

    A first run that emits two hundred findings is a first run that gets
    switched off.
    """
    (repo / "src" / "app" / "legacy.py").write_text("def old():\n    return 1\n",
                                                    encoding="utf-8")
    drift = atlas.reflexion(repo, added=[], removed=[])

    assert drift.divergent == ()
    assert not drift
    assert drift.standing >= 1


def test_a_document_naming_a_path_that_still_exists_is_silent(repo):
    """`store.py` is named and present. Naming a live file is not drift."""
    drift = atlas.reflexion(repo, added=[], removed=[])
    assert drift.absent == ()


def test_adding_a_test_file_is_not_a_module(repo):
    """Every task writes tests. None of them belong on an architecture map."""
    (repo / "tests" / "test_cache.py").write_text("def test_x():\n    assert True\n",
                                                  encoding="utf-8")
    drift = atlas.reflexion(repo, added=["tests/test_cache.py"], removed=[])
    assert drift.divergent == ()


def test_third_party_imports_are_not_architecture_edges(repo):
    """`import os` is a fact about Python, not about this repository."""
    model = atlas.source_model(repo)
    assert model["src/app/core.py"].imports == {"src/app/store.py"}, model["src/app/core.py"].imports


def test_relative_imports_resolve_to_the_sibling(tmp_path):
    """`from .store import load` is how a package actually writes it."""
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "app" / "store.py").write_text(STORE, encoding="utf-8")
    (tmp_path / "app" / "core.py").write_text(
        "from .store import load\n\n\ndef run():\n    return load()\n", encoding="utf-8")
    model = atlas.source_model(tmp_path)
    assert model["app/core.py"].imports == {"app/store.py"}


# --- the half that puts it in front of the agent ----------------------------

def test_the_neighbourhood_names_who_depends_on_you(repo):
    said = atlas.neighbourhood(repo, "src/app/store.py")
    assert "imported by src/app/core.py" in said, said
    assert "ARCHITECTURE.md" in said, said


def test_a_generated_map_names_every_module(repo):
    """The first document, for the repositories that have none."""
    text = atlas.initial_map(repo)
    assert "src/app/core.py" in text and "src/app/store.py" in text
    assert "tests/test_core.py" not in text

    (repo / "ARCHITECTURE.md").write_text(text, encoding="utf-8")
    assert not atlas.reflexion(repo, added=["src/app/core.py"], removed=[])


def test_a_design_note_does_not_count_as_the_map(repo):
    """Found by running this against its own repository.

    `core/radius.py` came back documented because the design note proposing it
    mentions it by name. Being discussed in `docs/design/` is not being on the
    architecture map, and if prose can discharge the check then writing about a
    module is as good as drawing it — which is the exact staleness this exists
    to catch.

    Forward — the design note still counts as documentation, so a stale
    reference in it is still reported. Adversarially — it cannot discharge a
    module's absence from the map.
    """
    (repo / "docs" / "design").mkdir(parents=True)
    (repo / "docs" / "design" / "cache.md").write_text(
        "We will add `src/app/cache.py`, and `src/app/store.py` feeds it.\n",
        encoding="utf-8")
    (repo / "src" / "app" / "cache.py").write_text("def get():\n    return None\n",
                                                   encoding="utf-8")

    drift = atlas.reflexion(repo, added=["src/app/cache.py"], removed=[])
    assert drift.divergent == ("src/app/cache.py",), drift.divergent
    assert "docs/design/cache.md" in drift.documents

    (repo / "src" / "app" / "store.py").unlink()
    stale = atlas.reflexion(repo, added=[], removed=["src/app/store.py"])
    assert ("docs/design/cache.md", "src/app/store.py") in stale.absent, stale.absent


def test_the_end_report_names_the_drift(tmp_path):
    """End to end: git says what changed, the report says what went stale.

    Forward — an untracked new module reaches the report. Adversarially —
    naming it in the map takes the line back out, so the report is responding
    to the document rather than to the file's existence.
    """
    import subprocess

    from core.ledger import Ledger
    from core.obligations import Claim, Risk
    from core.report import end_report

    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, capture_output=True)

    (tmp_path / "src" / "app").mkdir(parents=True)
    (tmp_path / "src" / "app" / "core.py").write_text(CORE, encoding="utf-8")
    (tmp_path / "src" / "app" / "store.py").write_text(STORE, encoding="utf-8")
    (tmp_path / "ARCHITECTURE.md").write_text(DOC, encoding="utf-8")
    git("init", "-q")
    git("config", "user.email", "probe@example.invalid")
    git("config", "user.name", "probe")
    git("add", "-A")
    git("commit", "-qm", "base")
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                          capture_output=True, text=True).stdout.strip()

    (tmp_path / "src" / "app" / "cache.py").write_text("def get():\n    return None\n",
                                                       encoding="utf-8")
    led = Ledger(root=tmp_path, claims=[Claim.BUG_FIXED], risk=Risk.LOW, base=base)
    text = end_report(led)
    assert "architecture: src/app/cache.py added" in text, text

    (tmp_path / "ARCHITECTURE.md").write_text(
        DOC + "\nCaching lives in `src/app/cache.py`.\n", encoding="utf-8")
    assert "architecture:" not in end_report(led)


# --- through the hook, which is where it has to actually arrive -------------

def _hook(event, payload):
    import json
    import subprocess
    import sys
    from pathlib import Path

    return subprocess.run(
        [sys.executable, "-m", "core.hook", event],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=Path(__file__).resolve().parents[1],
    )


def _context(result):
    import json

    if not result.stdout.strip():
        return ""
    return json.loads(result.stdout)["hookSpecificOutput"].get("additionalContext", "")


def test_the_brief_reaches_the_agent_before_the_first_edit(tmp_path):
    """The half of the request that computing a true map does not satisfy.

    Forward — editing a file the task has not touched hands over what imports
    it. Adversarially — the second edit of the same file says nothing, because
    a neighbourhood note on every edit is one nobody reads.
    """
    import subprocess

    (tmp_path / "src" / "app").mkdir(parents=True)
    (tmp_path / "src" / "app" / "core.py").write_text(CORE, encoding="utf-8")
    (tmp_path / "src" / "app" / "store.py").write_text(STORE, encoding="utf-8")
    (tmp_path / "ARCHITECTURE.md").write_text(DOC, encoding="utf-8")
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", "b"]):
        subprocess.run(["git", *args], cwd=tmp_path, capture_output=True)
    _hook("UserPromptSubmit", {"cwd": str(tmp_path), "prompt": "fix the app store loading bug"})

    target = str(tmp_path / "src" / "app" / "store.py")
    first = _context(_hook("PreToolUse", {"cwd": str(tmp_path), "tool_name": "Edit",
                                          "tool_input": {"file_path": target}}))
    assert "imported by src/app/core.py" in first, first
    assert "ARCHITECTURE.md" in first, first

    _hook("PostToolUse", {"cwd": str(tmp_path), "tool_name": "Edit",
                          "tool_input": {"file_path": target}})
    again = _context(_hook("PreToolUse", {"cwd": str(tmp_path), "tool_name": "Edit",
                                          "tool_input": {"file_path": target}}))
    assert "imported by" not in again, again
