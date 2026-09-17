"""The blast radius, in languages Python's `ast` cannot read.

`core/polyglot.py` is an **optional** backend: without the grammar pack these
tests skip and `core/radius.py` behaves exactly as it did when it was
Python-only. That fallback has its own test, which does not skip.

The fixture is `click-762c97ee` again - the case from this project's corpus
where an agent fixed `Choice` and never generalised to `DateTime` - rewritten in
TypeScript. The two classes never reference each other; the only thing linking
them is a shared base and a shared override.
"""

from __future__ import annotations

import subprocess

import pytest

from core import polyglot, radius

needs_grammars = pytest.mark.skipif(
    not polyglot.available(),
    reason="optional: pip install tree-sitter-language-pack")


def git(root, *args):
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0, f"git {' '.join(args)}: {done.stderr}"
    return done.stdout.strip()


TYPES = """export abstract class ParamType {
  convert(value: string): string {
    return value;
  }
}

export class Choice extends ParamType {
  convert(value: string): string {
    return String(value);
  }
}

export class DateTime extends ParamType {
  convert(value: string): string {
    return value;
  }
}
"""

USES = """import { Choice } from "./types";

export function build(raw: string): string {
  return new Choice().convert(raw);
}
"""

LEAF = """export function nobodyCallsThis(x: number): number {
  return x;
}
"""


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "probe@example.invalid")
    git(tmp_path, "config", "user.name", "probe")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "types.ts").write_text(TYPES, encoding="utf-8")
    (tmp_path / "src" / "uses.ts").write_text(USES, encoding="utf-8")
    (tmp_path / "src" / "leaf.ts").write_text(LEAF, encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def base_of(repo):
    return git(repo, "rev-parse", "HEAD")


def edit(repo, body):
    (repo / "src" / "types.ts").write_text(
        TYPES.replace("    return String(value);", body), encoding="utf-8")


# --- the fallback, which must hold whether or not grammars are installed -----

def test_without_the_grammar_pack_nothing_changes(repo, monkeypatch):
    """The promise that `core/` installs with nothing is kept.

    This test does not skip. With the optional backend reporting itself absent,
    a TypeScript file is simply not read - exactly as before polyglot existed -
    and no import error reaches the caller.
    """
    monkeypatch.setattr(polyglot, "available", lambda: False)
    assert radius.readable("src/types.ts") is False
    assert radius.readable("core/thing.py") is True
    assert radius._symbols(repo, "src/types.ts") == []

    edit(repo, "    return String(value).trim();")
    assert not radius.compute(repo, base_of(repo), ["src/types.ts"])


# --- forward ----------------------------------------------------------------

@needs_grammars
def test_a_typescript_sibling_is_found(repo):
    """click-762c97ee in TypeScript: fix Choice, never notice DateTime."""
    edit(repo, "    return String(value).trim();")
    found = radius.compute(repo, base_of(repo), ["src/types.ts"])

    assert found, "changed a method with a sibling and found nothing"
    assert "DateTime" in {s.owner for s in found.siblings}
    assert "you changed Choice.convert" in radius.wording(found, [])


@needs_grammars
def test_a_typescript_caller_is_found(repo):
    edit(repo, "    return String(value).trim();")
    found = radius.compute(repo, base_of(repo), ["src/types.ts"])
    assert "src/uses.ts" in found.callers, found.callers
    assert "src/types.ts" not in found.callers, "a file is not a caller of itself"


@needs_grammars
def test_bases_are_read_through_generics_and_interfaces(repo):
    """Real code writes `extends Base<T> implements Other`, not `extends Base`."""
    source = b"""export class Choice extends ParamType<string> implements Converter {
  convert(v: string): string { return v; }
}
"""
    got = {name: bases for name, _l, _e, owner, bases in polyglot.symbols("t.ts", source)
           if owner}
    # Order is not meaningful - sibling matching intersects sets - so assert
    # the content: both bases seen, and `<string>` stripped off the generic.
    assert set(got["convert"]) == {"ParamType", "Converter"}, got


# --- adversarial ------------------------------------------------------------

@needs_grammars
def test_the_base_class_is_not_a_sibling_of_its_own_subclass(repo):
    """`ParamType.convert` does not extend ParamType, so it is not a sibling."""
    edit(repo, "    return String(value).trim();")
    found = radius.compute(repo, base_of(repo), ["src/types.ts"])
    assert "ParamType" not in {s.owner for s in found.siblings}


@needs_grammars
def test_extending_error_does_not_make_every_error_a_sibling(repo):
    """Counted in a real TypeScript repository: 14 classes extend `Error`.

    Without `Error` in SCAFFOLD, changing one custom error makes every other
    custom error in the codebase a sibling - the `Generic` false positive from
    Python, arriving again in a new language.
    """
    (repo / "src" / "errors.ts").write_text(
        "export class NotFound extends Error {\n"
        "  describe(): string { return 'missing'; }\n"
        "}\n"
        "export class Timeout extends Error {\n"
        "  describe(): string { return 'slow'; }\n"
        "}\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "two unrelated errors")

    (repo / "src" / "errors.ts").write_text(
        "export class NotFound extends Error {\n"
        "  describe(): string { return 'gone'; }\n"
        "}\n"
        "export class Timeout extends Error {\n"
        "  describe(): string { return 'slow'; }\n"
        "}\n", encoding="utf-8")
    found = radius.compute(repo, base_of(repo), ["src/errors.ts"])
    assert "Timeout" not in {s.owner for s in found.siblings}, (
        "every custom error became a sibling of every other")


@needs_grammars
def test_a_leaf_nothing_references_is_silent(repo):
    (repo / "src" / "leaf.ts").write_text(
        "export function nobodyCallsThis(x: number): number {\n  return x + 1;\n}\n",
        encoding="utf-8")
    found = radius.compute(repo, base_of(repo), ["src/leaf.ts"])
    assert not found


@needs_grammars
def test_a_language_it_does_not_know_is_read_as_nothing(repo):
    """Silence, not a guess. A grammar absent from the table is not read."""
    assert polyglot.language_of("main.zig") == ""
    assert polyglot.symbols("main.zig", b"const x = 1;") == []
    assert radius.readable("main.zig") is False
