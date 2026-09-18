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


# --- every language in the table, proven rather than wired ------------------

# Each case is the same shape: two types sharing a base and a method (the
# sibling case), plus a free function (the caller case). `siblings` names the
# owners that must come back sharing a base; `tops` the module-level names.
CASES = {
    "x.ts": (b"""export class Choice extends ParamType { convert(v: string) { return v; } }
export class DateTime extends ParamType { convert(v: string) { return v; } }
export function buildUrl(p: string) { return p; }
export const toSlug = (s: string) => s;
""", {"Choice", "DateTime"}, {"buildUrl", "toSlug"}),
    "x.tsx": (b"""export class Modal extends Base { open(): void {} }
export class Drawer extends Base { open(): void {} }
export const Card = (p: Props) => null;
""", {"Modal", "Drawer"}, {"Card"}),
    "x.js": (b"""export class Choice extends ParamType { convert(v) { return v; } }
export class DateTime extends ParamType { convert(v) { return v; } }
export function buildUrl(p) { return p; }
""", {"Choice", "DateTime"}, {"buildUrl"}),
    "X.java": (b"""public class Choice extends ParamType { public String convert(String v) { return v; } }
public class DateTime extends ParamType { public String convert(String v) { return v; } }
""", {"Choice", "DateTime"}, set()),
    "x.rb": (b"""class Choice < ParamType
  def convert(v)
    v
  end
end
class DateTime < ParamType
  def convert(v)
    v
  end
end
def build_url(p)
  p
end
""", {"Choice", "DateTime"}, {"build_url"}),
    "x.php": (b"""<?php
class Choice extends ParamType { public function convert($v) { return $v; } }
class DateTime extends ParamType { public function convert($v) { return $v; } }
function buildUrl($p) { return $p; }
""", {"Choice", "DateTime"}, {"buildUrl"}),
    "X.cs": (b"""public class Choice : ParamType { public string Convert(string v) { return v; } }
public class DateTime : ParamType { public string Convert(string v) { return v; } }
""", {"Choice", "DateTime"}, set()),
    "x.rs": (b"""impl ParamType for Choice { fn convert(&self) -> String { String::new() } }
impl ParamType for DateTime { fn convert(&self) -> String { String::new() } }
pub fn build_url(p: &str) -> String { p.to_string() }
""", {"Choice", "DateTime"}, {"build_url"}),
}


@needs_grammars
@pytest.mark.parametrize("path", sorted(CASES))
def test_each_language_yields_owners_bases_and_free_functions(path):
    """Wired is not proven, and four of these were wrong when first written.

    Go lost every method, because it attaches them by receiver at the top level.
    Rust named the **trait** as the owner, which would have grouped siblings by
    the wrong thing. PHP lost its bases, because it calls identifiers `name`.
    C# read nothing at all, because the grammar is `csharp` and the table said
    `c_sharp` - the error handling degraded to silence, correctly, and hid it.
    """
    source, want_siblings, want_tops = CASES[path]
    got = polyglot.symbols(path, source)
    assert got, f"{path}: nothing extracted at all"

    tops = {name for name, _l, _e, owner, _b in got if not owner}
    assert want_tops <= tops, f"{path}: missing free functions {want_tops - tops}"

    shared = {owner for _n, _l, _e, owner, bases in got if owner and bases}
    assert want_siblings <= shared, (
        f"{path}: expected {want_siblings} to share a base, got {shared}")


@needs_grammars
def test_go_offers_callers_rather_than_siblings(path="x.go"):
    """Go has no syntactic inheritance, so it gets the honest half only.

    A method is owned by its receiver and carries no bases, so two Go types
    implementing the same interface are not siblings by anything this can see.
    Saying so beats inventing a relationship out of a shared method name.
    """
    source = (b"package main\ntype Choice struct{}\n"
              b"func (c Choice) Convert(v string) string { return v }\n"
              b"func BuildUrl(p string) string { return p }\n")
    got = polyglot.symbols(path, source)
    owners = {owner: bases for _n, _l, _e, owner, bases in got if owner}
    assert owners == {"Choice": ()}, owners
    assert "BuildUrl" in {n for n, _l, _e, owner, _b in got if not owner}


@needs_grammars
def test_locals_inside_a_function_are_not_module_level_symbols():
    """Adversarially: otherwise every temporary variable is a blast radius."""
    source = (b"export function outer() {\n"
              b"  const helper = () => 1;\n"
              b"  function inner() { return 2; }\n"
              b"  return helper() + inner();\n}\n")
    tops = {n for n, _l, _e, owner, _b in polyglot.symbols("x.ts", source) if not owner}
    assert tops == {"outer"}, tops


@needs_grammars
def test_a_changed_free_function_finds_its_callers(tmp_path):
    """The half that matters on a functional codebase, which most TS is.

    Reading only classes made this case silent: a repository of exported
    functions had no changed symbols at all, so no callers, so nothing. The
    repository that prompted polyglot support is exactly that shape - 14 classes
    extending `Error` and almost no other inheritance - so "who uses this" is
    the whole of what it can offer there.
    """
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "probe@example.invalid")
    git(tmp_path, "config", "user.name", "probe")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "url.ts").write_text(
        "export function buildUrl(p: string): string {\n  return p;\n}\n", encoding="utf-8")
    (tmp_path / "src" / "api.ts").write_text(
        'import { buildUrl } from "./url";\n'
        "export async function fetchJob(id: string) {\n"
        "  return fetch(buildUrl(id));\n}\n", encoding="utf-8")
    (tmp_path / "src" / "unrelated.ts").write_text(
        "export function formatDate(d: Date): string {\n  return d.toISOString();\n}\n",
        encoding="utf-8")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    base = git(tmp_path, "rev-parse", "HEAD")

    (tmp_path / "src" / "url.ts").write_text(
        "export function buildUrl(p: string): string {\n  return p.trim();\n}\n",
        encoding="utf-8")
    found = radius.compute(tmp_path, base, ["src/url.ts"])

    assert {s.name for s in found.changed} == {"buildUrl"}, found.changed
    assert "src/api.ts" in found.callers, found.callers
    # adversarial: a file that merely exists nearby is not a caller
    assert "src/unrelated.ts" not in found.callers, found.callers
    assert "1 file using it" in radius.wording(found, [])


@needs_grammars
def test_a_function_inside_a_block_is_not_module_level_api():
    """Where the transparency gate actually bites.

    The locals test above passes with or without it, because emitting a
    function stops the descent anyway - flipping it proved that probe vacuous.
    A function declared inside an `if` is the case that needs the gate: without
    it `debugOnly` and `secret` come back as module-level names, and a blast
    radius starts reporting conditional scaffolding as public surface.
    """
    source = (b"if (process.env.DEBUG) {\n"
              b"  function debugOnly() { return 1; }\n"
              b"  const secret = () => 2;\n"
              b"}\n"
              b"export function realApi() { return 3; }\n")
    tops = {n for n, _l, _e, owner, _b in polyglot.symbols("x.ts", source) if not owner}
    assert tops == {"realApi"}, tops


# --- the import graph, for the half that fires 47% of the time --------------

@pytest.fixture
def monorepo(tmp_path):
    """The shape that prompted this: workspaces, barrels, scoped packages."""
    (tmp_path / "packages" / "core" / "src").mkdir(parents=True)
    (tmp_path / "apps" / "web" / "src").mkdir(parents=True)
    (tmp_path / "packages" / "core" / "package.json").write_text(
        '{"name": "@acme/core"}', encoding="utf-8")
    (tmp_path / "packages" / "core" / "src" / "index.ts").write_text(
        'export * from "./rate";\n', encoding="utf-8")
    (tmp_path / "packages" / "core" / "src" / "rate.ts").write_text(
        "export const limit = 1;\n", encoding="utf-8")
    (tmp_path / "apps" / "web" / "src" / "api.ts").write_text(
        'import { limit } from "@acme/core";\n'
        'import { helper } from "./util";\n'
        'import fetch from "node-fetch";\n', encoding="utf-8")
    (tmp_path / "apps" / "web" / "src" / "util.ts").write_text(
        "export const helper = 1;\n", encoding="utf-8")
    return tmp_path


@needs_grammars
def test_a_workspace_import_resolves_across_packages(monorepo):
    """`@acme/core` is a path only because some package.json claims that name.

    Without reading those, every cross-package edge in a monorepo is invisible,
    which is most of the interesting ones.
    """
    from core import atlas

    model = atlas.source_model(monorepo)
    assert "packages/core/src/index.ts" in model["apps/web/src/api.ts"].imports


@needs_grammars
def test_relative_and_barrel_imports_resolve(monorepo):
    """TypeScript writes no extension, and a directory may mean its index."""
    from core import atlas

    model = atlas.source_model(monorepo)
    assert "apps/web/src/util.ts" in model["apps/web/src/api.ts"].imports
    assert "packages/core/src/rate.ts" in model["packages/core/src/index.ts"].imports


@needs_grammars
def test_a_dependency_outside_the_repository_is_not_an_edge(monorepo):
    """Adversarially: `node-fetch` is not this repository's architecture.

    The same rule Python already had - `import os` is a fact about the
    language, not about the project.
    """
    from core import atlas

    edges = atlas.source_model(monorepo)["apps/web/src/api.ts"].imports
    assert not any("node-fetch" in e or "node_modules" in e for e in edges), edges


@needs_grammars
def test_the_brief_reaches_a_typescript_file(monorepo):
    """The half with a measured firing rate, now in the language that needed it."""
    from core import atlas

    said = atlas.neighbourhood(monorepo, "packages/core/src/index.ts")
    assert "imported by apps/web/src/api.ts" in said, said
    assert "it imports packages/core/src/rate.ts" in said, said


@needs_grammars
def test_divergence_stays_python_only_on_purpose(monorepo):
    """Adversarially, and the distinction is deliberate.

    The graph is information; divergence is an obligation that says a map
    *should* have named this. On five upstream repositories the drift check
    fires on 0 of 23 commits because mature libraries add tests rather than
    modules - a TypeScript project adding files constantly is the opposite case,
    on a signal whose noise has never been measured. This gate blocked 75% of
    runs once on exactly that mistake, so the obligation did not grow with the
    graph.
    """
    from core import atlas

    (monorepo / "ARCHITECTURE.md").write_text("Core lives in packages/core.\n",
                                              encoding="utf-8")
    drift = atlas.reflexion(monorepo, added=["apps/web/src/brand-new.ts"], removed=[])
    assert drift.divergent == (), "a TypeScript file was demanded onto the map"


@needs_grammars
def test_importing_a_directory_resolves_to_its_index(monorepo):
    """`import { x } from "./handlers"` where handlers/ holds index.ts.

    Flipping the index fallback showed the tests above never needed it: they
    import files, and the extension loop covers those. A directory import is
    what the fallback is for, and it is how most TypeScript codebases group a
    folder behind one entry point.
    """
    from core import atlas

    (monorepo / "apps" / "web" / "src" / "handlers").mkdir()
    (monorepo / "apps" / "web" / "src" / "handlers" / "index.ts").write_text(
        "export const handle = 1;\n", encoding="utf-8")
    (monorepo / "apps" / "web" / "src" / "server.ts").write_text(
        'import { handle } from "./handlers";\n', encoding="utf-8")

    model = atlas.source_model(monorepo)
    assert "apps/web/src/handlers/index.ts" in model["apps/web/src/server.ts"].imports


@needs_grammars
def test_a_repository_too_large_says_so_rather_than_vanishing(monorepo):
    """Silence is the failure this project keeps rediscovering.

    The cap was 1200, sized from Python's `ast` at ~6ms a module. tree-sitter
    measures 3.8ms, so a 1,700-file TypeScript repository blew past a limit set
    for a different parser and the graph silently returned nothing - on exactly
    the kind of repository it was built for. The number is now taken from the
    measurement, and exceeding it is recorded instead of hidden.
    """
    from core import atlas, blindspots

    assert atlas.source_model(monorepo, limit=1) == {}
    spots = [b for b in blindspots.read(monorepo)
             if b["kind"] == "repository too large for the import graph"]
    assert spots, "the graph gave up without saying so"
    assert "limit 1" in spots[-1]["detail"]
