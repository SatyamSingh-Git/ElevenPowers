"""The blast radius, and the six ways it must stay quiet.

Design: `docs/design/blast-radius.md`. A radius that fires on everything and one
that fires on nothing are both indistinguishable from the feature being absent,
so the adversarial cases outnumber the forward ones on purpose.

The fixture is `click-762c97ee` in miniature — the real case from this
project's own corpus, where an agent fixed `Choice` and never generalised to
`DateTime`. The two classes never reference each other; the only thing linking
them is a shared base and a shared override, which is exactly what a text search
cannot see and what this has to.
"""

from __future__ import annotations

import subprocess

import pytest

from core import radius


def git(root, *args):
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, f"git {' '.join(args)}: {done.stderr}"
    return done.stdout.strip()


TYPES = '''class ParamType:
    def convert(self, value):
        return value


class Choice(ParamType):
    def convert(self, value):
        return str(value)


class DateTime(ParamType):
    def convert(self, value):
        return value
'''

USES = '''from types_mod import Choice


def build(raw):
    return Choice().convert(raw)
'''

LEAF = '''def nobody_calls_this(x):
    return x
'''


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "probe@example.invalid")
    git(tmp_path, "config", "user.name", "probe")
    (tmp_path / "tests").mkdir()
    (tmp_path / "types_mod.py").write_text(TYPES, encoding="utf-8")
    (tmp_path / "uses.py").write_text(USES, encoding="utf-8")
    (tmp_path / "leaf.py").write_text(LEAF, encoding="utf-8")
    (tmp_path / "tests" / "test_types_mod.py").write_text(
        "def test_convert():\n    assert True\n", encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def base_of(repo):
    return git(repo, "rev-parse", "HEAD")


# --- forward ----------------------------------------------------------------

def test_a_sibling_implementation_is_found(repo):
    """The click-762c97ee case: fix Choice, never notice DateTime."""
    (repo / "types_mod.py").write_text(
        TYPES.replace("        return str(value)", "        return str(value).strip()"),
        encoding="utf-8")
    found = radius.compute(repo, base_of(repo), ["types_mod.py"])

    assert found, "changed a method with a sibling and found nothing"
    # ParamType is the base, not a sibling: its own `convert` does not inherit
    # from ParamType, so it is not another implementation of the interface.
    assert {s.owner for s in found.siblings} == {"DateTime"}
    assert "you changed Choice.convert" in radius.wording(found, [])


def test_a_caller_of_a_changed_top_level_symbol_is_found(repo):
    """A changed function, and the file that uses it."""
    (repo / "types_mod.py").write_text(
        TYPES.replace("        return str(value)", "        return str(value).strip()"),
        encoding="utf-8")
    found = radius.compute(repo, base_of(repo), ["types_mod.py"])
    # `uses.py` imports and calls Choice, which is among the changed symbols.
    assert "uses.py" in found.callers, found.callers
    # and the file that defines it is not reported as a caller of itself
    assert "types_mod.py" not in found.callers


def test_the_covering_test_is_named(repo):
    (repo / "types_mod.py").write_text(
        TYPES.replace("        return str(value)", "        return str(value).strip()"),
        encoding="utf-8")
    found = radius.compute(repo, base_of(repo), ["types_mod.py"])
    tests = radius.covering(repo, found)
    assert "tests/test_types_mod.py" in tests, tests
    assert "Closest cover" in radius.wording(found, tests)


# --- adversarial ------------------------------------------------------------

def test_a_leaf_nothing_references_is_silent(repo):
    """Changing something nobody depends on must say nothing at all."""
    (repo / "leaf.py").write_text(
        "def nobody_calls_this(x):\n    return x + 1\n", encoding="utf-8")
    found = radius.compute(repo, base_of(repo), ["leaf.py"])
    assert not found
    assert radius.wording(found, []) == ""


def test_changing_only_a_test_is_silent(repo):
    """Most tasks write a test. None of them need warning about it."""
    (repo / "tests" / "test_types_mod.py").write_text(
        "def test_convert():\n    assert 1 == 1\n", encoding="utf-8")
    found = radius.compute(repo, base_of(repo), ["tests/test_types_mod.py"])
    assert not found


def test_a_shared_name_without_a_shared_base_is_not_a_sibling(repo):
    """`run` on two unrelated classes is a coincidence, not an interface.

    This is the false positive the whole check has to avoid: match on the name
    alone and every project with two `convert` methods lights up.
    """
    (repo / "other.py").write_text(
        "class Unrelated:\n    def convert(self, value):\n        return value\n",
        encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "an unrelated class with the same method name")

    (repo / "types_mod.py").write_text(
        TYPES.replace("        return str(value)", "        return str(value).strip()"),
        encoding="utf-8")
    found = radius.compute(repo, base_of(repo), ["types_mod.py"])
    assert "Unrelated" not in {s.owner for s in found.siblings}


def test_a_dependent_with_no_test_demands_nothing(repo):
    """Name it, require nothing. `surface.py`'s rule, applied here."""
    (repo / "tests" / "test_types_mod.py").unlink()
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "no tests at all")

    (repo / "types_mod.py").write_text(
        TYPES.replace("        return str(value)", "        return str(value).strip()"),
        encoding="utf-8")
    found = radius.compute(repo, base_of(repo), ["types_mod.py"])
    assert found, "the dependents are still real"
    assert radius.covering(repo, found) == []
    assert "no test here covers them" in radius.wording(found, [])


def test_only_the_symbol_that_moved_counts(repo):
    """A file defines many things; the task changed one.

    Without line ranges every symbol in an edited file would be reported, and
    the radius of a one-line fix would be the whole module.
    """
    (repo / "types_mod.py").write_text(
        TYPES.replace("        return str(value)", "        return str(value).strip()"),
        encoding="utf-8")
    found = radius.compute(repo, base_of(repo), ["types_mod.py"])
    moved = {f"{s.owner}.{s.name}" if s.owner else s.name for s in found.changed}
    assert "Choice.convert" in moved
    assert "DateTime.convert" not in moved, moved


def test_no_base_commit_means_no_claim(repo):
    """Outside a repository, or before anything is committed, say nothing."""
    assert not radius.compute(repo, "", ["types_mod.py"])


# --- generics, which is how real code actually writes bases -----------------

GENERIC = '''import abc
import typing as t

T = t.TypeVar("T")


class ParamType(t.Generic[T], abc.ABC):
    def convert(self, value):
        return value


class Choice(ParamType[T], t.Generic[T]):
    def convert(self, value):
        return str(value)


class DateTime(ParamType[str]):
    def convert(self, value):
        return value


class Unrelated(t.Generic[T]):
    def convert(self, value):
        return value
'''


@pytest.fixture
def generic_repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "probe@example.invalid")
    git(tmp_path, "config", "user.name", "probe")
    (tmp_path / "generic_mod.py").write_text(GENERIC, encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "generics, as real code writes them")
    return tmp_path


def test_a_subscripted_base_is_still_a_base(generic_repo):
    """`ParamType[T]` is an `ast.Subscript`, not a `Name`.

    Reading only `Name` found no bases at all on the real click repository, so
    no siblings, so nothing — the check failed silently on the one case it was
    built for, and the fixture could not show it because fixtures write
    `class Choice(ParamType)`.
    """
    bases = {s.owner: s.bases for s in radius._symbols(generic_repo, "generic_mod.py")
             if s.name == "convert"}
    assert bases["Choice"] == ("ParamType", "Generic"), bases
    assert bases["DateTime"] == ("ParamType",), bases


def test_a_scaffolding_base_is_not_a_shared_interface(generic_repo):
    """Both directions, because `Generic` matches nearly everything.

    Forward — `DateTime` is still found, which is the click-762c97ee case.
    Adversarially — `ParamType`, the base class itself, and `Unrelated`, which
    shares only `t.Generic`, are not siblings. On real click this fired: every
    generic class defining `convert` came back, the base class included.
    """
    (generic_repo / "generic_mod.py").write_text(
        GENERIC.replace("        return str(value)", "        return str(value).strip()"),
        encoding="utf-8")
    found = radius.compute(generic_repo, base_of(generic_repo), ["generic_mod.py"])
    assert {s.owner for s in found.siblings} == {"DateTime"}, found.siblings


def test_the_named_cover_is_something_you_can_actually_run(repo):
    """Found by measuring on real commits, not by the fixture.

    `TEST_NAME` matches the *directory*, so attrs' `tests/test_mypy.yml` came
    back as the closest cover, and `tests/__init__.py` came back for eight
    callers. Naming a file that cannot be run is worse than naming none, since
    the whole point of the line is to tell you what to run next.

    Forward — the real test file is still named. Adversarially — the YAML
    fixture and the package marker are not.
    """
    (repo / "tests" / "test_types_mod.yml").write_text("cases: []\n", encoding="utf-8")
    (repo / "tests" / "__init__.py").write_text("", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "data and a package marker under tests/")

    (repo / "types_mod.py").write_text(
        TYPES.replace("        return str(value)", "        return str(value).strip()"),
        encoding="utf-8")
    found = radius.compute(repo, base_of(repo), ["types_mod.py"])
    cover = radius.covering(repo, found)

    assert "tests/test_types_mod.py" in cover, cover
    assert not [p for p in cover if p.endswith((".yml", "__init__.py"))], cover
