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
    ".cs": "c_sharp",
}


@dataclass(frozen=True)
class Shape:
    """Which node types carry the facts a blast radius is built from."""

    containers: tuple[str, ...]
    """A class, struct, interface or impl block - the thing that has methods."""
    methods: tuple[str, ...]
    bases: tuple[str, ...]
    """Nodes holding what it inherits from. Their identifiers are the bases."""


_CLASSY = Shape(
    containers=("class_declaration", "interface_declaration", "abstract_class_declaration"),
    methods=("method_definition", "method_signature", "function_declaration"),
    bases=("class_heritage", "extends_clause", "implements_clause", "extends_type_clause"),
)

SHAPES = {
    "typescript": _CLASSY,
    "tsx": _CLASSY,
    "javascript": _CLASSY,
    "java": Shape(
        containers=("class_declaration", "interface_declaration"),
        methods=("method_declaration",),
        bases=("superclass", "super_interfaces"),
    ),
    "c_sharp": Shape(
        containers=("class_declaration", "interface_declaration", "struct_declaration"),
        methods=("method_declaration",),
        bases=("base_list",),
    ),
    "rust": Shape(
        containers=("impl_item", "struct_item", "trait_item"),
        methods=("function_item",),
        bases=("trait",),
    ),
    "go": Shape(
        containers=("type_declaration",),
        methods=("method_declaration",),
        bases=(),
    ),
    "ruby": Shape(
        containers=("class", "module"),
        methods=("method",),
        bases=("superclass",),
    ),
    "php": Shape(
        containers=("class_declaration", "interface_declaration"),
        methods=("method_declaration",),
        bases=("base_clause", "class_interface_clause"),
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
                         "scoped_type_identifier", "qualified_type"):
            text = source[here.start_byte:here.end_byte].decode("utf-8", "replace")
            # `ParamType<string>` inherits from `ParamType`. The parameter is
            # not a base, and treating it as one made every generic class a
            # sibling of every other when this was done for Python.
            found.append(text.split("<")[0].split(".")[-1].strip())
        stack.extend(here.children)
    return [f for f in found if f]


def symbols(path: str, source: bytes) -> list[tuple[str, int, int, str, tuple[str, ...]]]:
    """`(name, line, end_line, owner, bases)` for each method and container.

    Shaped to match what `radius._symbols` builds from Python's `ast`, so the
    caller does not branch on language after this point.
    """
    tree, shape = _parse(path, source)
    if tree is None:
        return []

    out: list[tuple[str, int, int, str, tuple[str, ...]]] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type in shape.containers:
            owner = _name_of(node, source)
            bases: list[str] = []
            for child in node.children:
                if child.type in shape.bases:
                    bases.extend(_identifiers(child, source))
                # TypeScript nests extends/implements inside class_heritage.
                for grand in child.children:
                    if grand.type in shape.bases:
                        bases.extend(_identifiers(grand, source))
            kept = tuple(dict.fromkeys(b for b in bases if b and b != owner))
            out.append((owner, node.start_point[0] + 1, node.end_point[0] + 1, "", ()))
            for method in _descendants(node, shape.methods):
                out.append((_name_of(method, source),
                            method.start_point[0] + 1, method.end_point[0] + 1,
                            owner, kept))
            continue
        stack.extend(node.children)
    return [s for s in out if s[0]]


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
