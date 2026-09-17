"""Symbols and inheritance for languages Python's `ast` cannot read.

`core/radius.py` finds what else implements or calls the thing you changed, and
until now it could only do that for Python, because `ast` is exact, free and in
the standard library. Pointed at a real TypeScript repository it had nothing to
say about 1,463 files.

**The borrow.** Aider's `repomap.py` (Apache-2.0) is the best repository symbol
graph in the field by this project's own survey, and its answer to polyglot is
the same one Continue and OpenCode reached: **tree-sitter**. There is no clever
alternative and none of those projects found one. What is taken here is the
approach and the grammar pack, not the code - Aider extracts *tags*
(definitions and references) for context selection under a token budget, and
carries no inheritance, which is the one thing a sibling check needs.

**Optional, and silent when absent.** `core/` held zero third-party imports so
that the plugin installs with nothing, and that promise is kept: the import
below is guarded, every entry point answers "no" when it fails, and
`core/radius.py` falls back to Python-only exactly as before. A user who wants
polyglot runs `pip install tree-sitter-language-pack`; a user who does not is
not asked to.

**Per-language, because grammars differ.** `class_declaration` in TypeScript is
`class_specifier` in C++ and `impl_item` in Rust, and the node holding the base
class has a different name in each. The table below is small, explicit and
tested rather than clever, and a language missing from it is simply not read.
"""

from __future__ import annotations

from dataclasses import dataclass

try:  # pragma: no cover - exercised by the absence test, not by import
    from tree_sitter_language_pack import get_parser as _get_parser
except Exception:                                          # noqa: BLE001
    _get_parser = None

# Extension to grammar. Only languages whose node names are in `SHAPES` below,
# because reading a grammar this module does not understand would produce
# confident nonsense rather than silence.
LANGUAGES = {
    ".ts": "typescript", ".mts": "typescript", ".cts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
}


@dataclass(frozen=True)
class Shape:
    """Which node types carry the facts a blast radius is built from."""

    containers: tuple[str, ...]
    """A class, struct, interface or impl block - the thing that has methods."""
    methods: tuple[str, ...]
    bases: tuple[str, ...]
    """Nodes holding what it inherits from. Their identifiers are the bases."""
    dialect: str = ""
    """`go` or `rust`, where a method is not written inside its type.

    Go attaches by receiver - `func (c Choice) Convert()` sits at the top level
    - and Rust by `impl Trait for Type`. Both were read with the generic
    container rule first, and both came out wrong: Go lost every method, and
    Rust reported the **trait** as the owner, which would have grouped siblings
    by the wrong thing entirely.
    """
    functions: tuple[str, ...] = ()
    """Top-level callables and bindings, which is most of a modern codebase.

    Reading only classes made a functional TypeScript file come back with
    nothing: `export function buildUrl` and `export const toSlug` were both
    invisible, so nothing changed, so no callers, so silence. Most of the value
    on such a repository is "who uses this", and without these there is no
    "this" to find users of.
    """


_CLASSY = Shape(
    containers=("class_declaration", "interface_declaration", "abstract_class_declaration"),
    methods=("method_definition", "method_signature", "function_declaration"),
    bases=("class_heritage", "extends_clause", "implements_clause", "extends_type_clause"),
    functions=("function_declaration", "generator_function_declaration", "variable_declarator"),
)

SHAPES = {
    "typescript": _CLASSY,
    "tsx": _CLASSY,
    "javascript": _CLASSY,
    "java": Shape(
        containers=("class_declaration", "interface_declaration"),
        methods=("method_declaration",),
        bases=("superclass", "super_interfaces"),
        functions=(),
    ),
    "csharp": Shape(
        containers=("class_declaration", "interface_declaration", "struct_declaration"),
        methods=("method_declaration",),
        bases=("base_list",),
        functions=(),
    ),
    "rust": Shape(
        containers=("impl_item", "struct_item", "trait_item"),
        methods=("function_item",),
        bases=(),
        dialect="rust",
        functions=("function_item",),
    ),
    "go": Shape(
        containers=("type_declaration",),
        methods=("method_declaration",),
        bases=(),
        dialect="go",
        functions=("function_declaration",),
    ),
    "ruby": Shape(
        containers=("class", "module"),
        methods=("method",),
        bases=("superclass",),
        functions=("method",),
    ),
    "php": Shape(
        containers=("class_declaration", "interface_declaration"),
        methods=("method_declaration",),
        bases=("base_clause", "class_interface_clause"),
        functions=("function_definition",),
    ),
}


def available() -> bool:
    """Is the optional grammar pack installed?"""
    return _get_parser is not None


def language_of(path: str) -> str:
    """The grammar for this file, or empty if this module does not read it."""
    dot = path.rfind(".")
    name = LANGUAGES.get(path[dot:].lower(), "") if dot >= 0 else ""
    return name if name in SHAPES else ""


def _parse(path: str, source: bytes):
    language = language_of(path)
    if not language or not available():
        return None, None
    try:
        return _get_parser(language).parse(source), SHAPES[language]
    except Exception:                                      # noqa: BLE001
        # A grammar that will not load, or source it cannot handle. Silence is
        # the honest answer: the caller falls back to knowing nothing about
        # this file rather than to a guess about it.
        return None, None


def _name_of(node, source: bytes) -> str:
    named = node.child_by_field_name("name")
    if named is not None:
        return source[named.start_byte:named.end_byte].decode("utf-8", "replace")
    for child in node.children:
        if child.type in ("identifier", "type_identifier", "constant", "property_identifier"):
            return source[child.start_byte:child.end_byte].decode("utf-8", "replace")
    return ""


def _identifiers(node, source: bytes) -> list[str]:
    found = []
    stack = [node]
    while stack:
        here = stack.pop()
        if here.type in ("identifier", "type_identifier", "constant", "generic_type",
                         "scoped_type_identifier", "qualified_type", "name"):
            text = source[here.start_byte:here.end_byte].decode("utf-8", "replace")
            # `ParamType<string>` inherits from `ParamType`. The parameter is
            # not a base, and treating it as one made every generic class a
            # sibling of every other when this was done for Python.
            found.append(text.split("<")[0].split(".")[-1].strip())
        stack.extend(here.children)
    return [f for f in found if f]


def symbols(path: str, source: bytes) -> list[tuple[str, int, int, str, tuple[str, ...]]]:
    """`(name, line, end_line, owner, bases)` for containers, methods and
    top-level callables.

    Shaped to match what `radius._symbols` builds from Python's `ast`, so the
    caller does not branch on language after this point.
    """
    tree, shape = _parse(path, source)
    if tree is None:
        return []
    out: list[tuple[str, int, int, str, tuple[str, ...]]] = []
    _walk(tree.root_node, source, shape, out, top=True)
    return [s for s in out if s[0]]


def _walk(node, source: bytes, shape: Shape, out: list, top: bool) -> None:
    """Descend, but not into bodies when looking for top-level names.

    `top` is what keeps a local `const helper = ...` inside a function from
    being reported as a module-level symbol. Containers and their methods are
    collected at any depth; free functions only where they are actually free.
    """
    for child in node.children:
        if shape.dialect == "go" and child.type == "method_declaration":
            # `func (c Choice) Convert(...)`. The owner is the receiver's type,
            # which sits in the first parameter list, not anywhere near the
            # type declaration. Go has no syntactic inheritance, so there are
            # no bases and therefore no siblings - callers are what it offers.
            out.append((_name_of(child, source),
                        child.start_point[0] + 1, child.end_point[0] + 1,
                        _go_receiver(child, source), ()))
            continue
        if shape.dialect == "rust" and child.type == "impl_item":
            owner, base = _rust_impl(child, source)
            for method in _descendants(child, shape.methods):
                out.append((_name_of(method, source),
                            method.start_point[0] + 1, method.end_point[0] + 1,
                            owner, (base,) if base else ()))
            continue
        if child.type in shape.containers:
            owner = _name_of(child, source)
            bases: list[str] = []
            for part in child.children:
                if part.type in shape.bases:
                    bases.extend(_identifiers(part, source))
                # TypeScript nests extends/implements inside `class_heritage`.
                for grand in part.children:
                    if grand.type in shape.bases:
                        bases.extend(_identifiers(grand, source))
            kept = tuple(dict.fromkeys(b for b in bases if b and b != owner))
            out.append((owner, child.start_point[0] + 1, child.end_point[0] + 1, "", ()))
            for method in _descendants(child, shape.methods):
                out.append((_name_of(method, source),
                            method.start_point[0] + 1, method.end_point[0] + 1,
                            owner, kept))
            continue
        if top and child.type in shape.functions:
            name = _name_of(child, source)
            if name:
                out.append((name, child.start_point[0] + 1, child.end_point[0] + 1, "", ()))
            continue        # its body holds locals, not module-level names
        # `export ...`, `lexical_declaration` and the like are wrappers: stay at
        # the top level through them, so `export const f = () => {}` is seen.
        _walk(child, source, shape, out,
              top and child.type in _TRANSPARENT)


# Nodes that wrap a declaration without being one, so passing through them does
# not mean descending into a body.
_TRANSPARENT = frozenset({
    "program", "source_file", "module", "translation_unit",
    "export_statement", "lexical_declaration", "variable_declaration",
    "declaration", "statement", "expression_statement",
    "namespace_declaration", "package_declaration", "class_body",
})


def _go_receiver(node, source: bytes) -> str:
    """The type a Go method hangs off, out of `(c Choice)`."""
    for child in node.children:
        if child.type == "parameter_list":
            for found in _descendants(child, ("type_identifier",)):
                return source[found.start_byte:found.end_byte].decode("utf-8", "replace")
            break
    return ""


def _rust_impl(node, source: bytes) -> tuple[str, str]:
    """`(type, trait)` for an impl block, which Rust writes trait-first.

    `impl ParamType for Choice` parses as two sibling `type_identifier` nodes
    either side of `for`, and reading the first as the owner - which the generic
    rule did - names the trait. The type is what owns the methods; the trait is
    what makes two types siblings.
    """
    names = [source[c.start_byte:c.end_byte].decode("utf-8", "replace")
             for c in node.children if c.type in ("type_identifier", "generic_type")]
    has_for = any(c.type == "for" for c in node.children)
    if has_for and len(names) >= 2:
        return names[-1].split("<")[0], names[0].split("<")[0]
    return (names[0].split("<")[0] if names else ""), ""


def _descendants(node, types: tuple[str, ...]):
    found, stack = [], list(node.children)
    while stack:
        here = stack.pop()
        if here.type in types:
            found.append(here)
            continue
        stack.extend(here.children)
    return found


def references(path: str, source: bytes) -> set[str]:
    """Identifiers this file mentions in code, for finding callers."""
    tree, _ = _parse(path, source)
    if tree is None:
        return set()
    seen: set[str] = set()
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type in ("identifier", "type_identifier", "property_identifier",
                         "constant", "shorthand_property_identifier"):
            seen.add(source[node.start_byte:node.end_byte].decode("utf-8", "replace"))
        stack.extend(node.children)
    return seen


# Module specifiers, for `core/atlas.py`. Deliberately the JS/TS family only:
# Go, Rust and Java resolve imports by rules of their own, and a shared guess
# would be wrong in three different ways at once.
IMPORTABLE = frozenset({"typescript", "tsx", "javascript"})


def imports(path: str, source: bytes) -> list[str]:
    """The module specifiers this file imports, exactly as written.

    `import x from "./y"`, `export {x} from "./y"`, `require("./y")` and a bare
    `import "./y"` all carry the specifier as the one string in the statement,
    so one rule reads every form. Resolving it to a file is the caller's job,
    because that depends on the project's layout rather than on its syntax.
    """
    if language_of(path) not in IMPORTABLE:
        return []
    tree, _ = _parse(path, source)
    if tree is None:
        return []
    found: list[str] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type in ("import_statement", "export_statement") or (
                node.type == "call_expression"
                and source[node.start_byte:node.start_byte + 7] == b"require"):
            for text in _descendants(node, ("string_fragment",)):
                found.append(source[text.start_byte:text.end_byte].decode("utf-8", "replace"))
            continue
        stack.extend(node.children)
    return [f for f in found if f]
