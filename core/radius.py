"""What else depends on the thing you just changed.

Design note: `docs/design/blast-radius.md`. The short version.

Agents fix one bug and make another: **16 to 37 percent of applied agent patches
break a pre-existing test**, and *recall grows near-linearly while precision
saturates* — they keep adding and stop preventing. This repository's own corpus
holds the case: `click-762c97ee`, where the agent fixed `Choice` and never
generalised to `DateTime`. PLAN §5.2 named the remedy — *sibling implementations
of the changed interface, callers with other argument types* — and it sat
unbuilt.

**Why this is computed rather than asked for.** The instinct is to demand a
plan. But constraint violation rises **0 to 78 percent across four compaction
rounds**, and soft organisational policy decays about **8.3 times faster** than
hard norms, so an instruction file is gone by the time it matters. And *the
negative impact of a bad plan is greater than no plan at all*, measured over
16,991 trajectories. Nothing here is asked of the agent's memory, so nothing can
be forgotten.

**Python through the standard library, everything else through tree-sitter.**
Python is read with `ast`: exact, free, and already installed. For other
languages there is no such thing, and the honest answer is the one Aider,
Continue and OpenCode all reached — **tree-sitter**. There is no clever
alternative and none of them found one.

That arrives through `core/polyglot.py` as an **optional** dependency, so the
promise that this plugin installs with nothing is kept. With
`tree-sitter-language-pack` present it reads TypeScript, TSX, JavaScript, Go,
Rust, Java, Ruby, PHP and C#; without it, this module behaves exactly as it did
when it was Python-only, and says so rather than guessing.

What is borrowed from Aider's `repomap.py` (Apache-2.0) is the approach, not the
code: it extracts *tags* — definitions and references — to select context under
a token budget, and carries no inheritance at all. A sibling is defined by a
shared base class, so that part had to be built.

**It names; it does not demand.** A dependent with no test covering it is
reported and nothing is required of it — `core/surface.py` exists because an
obligation nothing can discharge is a design error rather than a finding.
"""

from __future__ import annotations

import ast
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# `@@ -a,b +c,d @@` — the only part of a diff this needs. `-U0` keeps the
# ranges tight to what actually changed rather than three lines either side.
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@", re.MULTILINE)

# Names so common that sharing one says nothing about sharing an interface.
# A sibling still has to share a base class; this only trims the noise earlier.
PLAIN = frozenset({"run", "get", "set", "add", "main", "close", "read", "write",
                   "start", "stop", "update", "load", "save", "parse", "handle"})

# Bases that carry no behaviour contract, so sharing one means nothing.
# Real click writes `class ParamType(t.Generic[...], abc.ABC)` and
# `class Choice(ParamType[...], t.Generic[...])`: they intersect on `Generic`,
# which reported a base class as a sibling of its own subclass — and would make
# any two generic classes with a method name in common siblings. The fixture
# could not show this because fixtures write `class Choice(ParamType)`.
SCAFFOLD = frozenset({"Generic", "Protocol", "ABC", "ABCMeta", "object",
                      "Enum", "IntEnum", "StrEnum", "Flag", "IntFlag",
                      "NamedTuple", "TypedDict",
                      # The same trap in the other languages, found the same
                      # way - by counting real bases in a real repository. A
                      # TypeScript codebase there has fourteen classes
                      # extending `Error` and almost nothing else shared, so
                      # without this every custom error is a sibling of every
                      # other one the moment any of them changes.
                      "Error", "Exception", "RuntimeException", "Object",
                      "Component", "PureComponent", "HTMLElement", "Struct"})


@dataclass(frozen=True)
class Symbol:
    """A def or class, and where it lives."""
    name: str
    path: str
    line: int
    end: int
    owner: str = ""
    """The class this is a method of, empty for a top-level symbol."""
    bases: tuple[str, ...] = ()
    """The owning class's base names, which is what makes a sibling a sibling."""


@dataclass
class Radius:
    changed: list[Symbol] = field(default_factory=list)
    siblings: list[Symbol] = field(default_factory=list)
    """Other implementations of a changed method, under a shared base."""
    callers: list[str] = field(default_factory=list)
    """Files referencing a changed top-level symbol."""

    def __bool__(self) -> bool:
        return bool(self.siblings or self.callers)


def _git(root: Path, *args: str) -> str:
    try:
        done = subprocess.run(["git", *args], cwd=root, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout if done.returncode == 0 else ""


def changed_lines(root: Path, base: str, path: str) -> set[int]:
    """Line numbers this task altered in one file."""
    diff = _git(root, "diff", "-U0", base, "--", path)
    lines: set[int] = set()
    for match in HUNK.finditer(diff):
        start = int(match.group("start"))
        count = int(match.group("count") or 1)
        lines.update(range(start, start + count))
    if not diff and (root / path).is_file():
        # Untracked: the whole file is new, so all of it changed.
        lines.update(range(1, len((root / path).read_text(
            encoding="utf-8", errors="replace").splitlines()) + 1))
    return lines


def _base_name(node: ast.expr) -> str:
    """The name of a base class, through the forms real code actually uses.

    A fixture writes `class Choice(ParamType)`. Click writes
    `class Choice(ParamType[_ValueT_co], t.Generic[_ValueT_co])` and
    `class DateTime(ParamType[datetime])` — subscripted generics, where the base
    is an `ast.Subscript` and not a `Name` at all. Reading only `Name` found no
    bases on the real repository, so no siblings, so nothing: the check would
    have failed silently on the very case it was built for.

    Dotted bases (`module.Base`) resolve to the final attribute, which is what a
    subclass in another file writes when it imports differently.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return ""


def readable(path: str) -> bool:
    """Can symbols be extracted from this file at all?

    Python always, through the standard library. Everything else only when the
    optional grammar pack is installed - see `core/polyglot.py`. Without it this
    module behaves exactly as it did when it was Python-only.
    """
    from . import polyglot

    if path.endswith(".py"):
        return True
    return polyglot.available() and bool(polyglot.language_of(path))


def _symbols(root: Path, path: str) -> list[Symbol]:
    """Every def and class in one file, with its owner and bases."""
    from . import polyglot

    if not path.endswith(".py"):
        try:
            source = (root / path).read_bytes()
        except OSError:
            return []
        return [Symbol(name, path, line, end, owner, bases)
                for name, line, end, owner, bases in polyglot.symbols(path, source)]

    try:
        tree = ast.parse((root / path).read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        return []

    found: list[Symbol] = []

    def walk(node, owner: str = "", bases: tuple[str, ...] = ()) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found.append(Symbol(child.name, path, child.lineno,
                                    getattr(child, "end_lineno", child.lineno),
                                    owner, bases))
                continue
            if isinstance(child, ast.ClassDef):
                names = tuple(n for n in (_base_name(b) for b in child.bases) if n)
                found.append(Symbol(child.name, path, child.lineno,
                                    getattr(child, "end_lineno", child.lineno)))
                walk(child, child.name, names)
                continue
            walk(child, owner, bases)

    walk(tree)
    return found


def _references(root: Path, path: str) -> set[str]:
    """Names this file actually refers to, in code rather than in prose.

    A `Name` or an attribute's final part. Parsed rather than grepped, so a
    mention inside a docstring, a comment or a string literal does not count —
    which is most of what a text search would have returned.
    """
    from . import polyglot

    if not path.endswith(".py"):
        try:
            return polyglot.references(path, (root / path).read_bytes())
        except OSError:
            return set()

    try:
        tree = ast.parse((root / path).read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        return set()
    seen: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            seen.add(node.id)
        elif isinstance(node, ast.Attribute):
            seen.add(node.attr)
    return seen


def _python_files(root: Path, limit: int = 4000) -> list[str]:
    from .surface import _walk

    return [p for p in _walk(root) if readable(p)][:limit]


def compute(root: Path, base: str, touched: list[str]) -> Radius:
    """What the changed code shares its behaviour with.

    Test-only changes produce nothing: editing a test is not a change whose
    blast radius anyone needs warning about, and treating it as one would fire
    on every task that writes a test, which is most of them.
    """
    from .surface import TEST_NAME

    edited = [p for p in touched
              if readable(p) and not TEST_NAME.search(p) and (root / p).is_file()]
    if not edited or not base:
        return Radius()

    changed: list[Symbol] = []
    for path in edited:
        lines = changed_lines(root, base, path)
        if not lines:
            continue
        for symbol in _symbols(root, path):
            # The symbol's own span, so a file with forty defs contributes the
            # one that moved rather than all of them.
            if any(symbol.line <= n <= symbol.end for n in lines):
                changed.append(symbol)
    if not changed:
        return Radius()

    methods = {s.name: s for s in changed if s.owner and s.name not in PLAIN}
    interfaces = {b for s in changed if s.owner for b in s.bases} - SCAFFOLD
    wanted = {s.name for s in changed if not s.owner}
    here = {s.path for s in changed}

    moved = {(s.path, s.owner, s.name) for s in changed}
    siblings: list[Symbol] = []
    callers: list[str] = []
    for path in _python_files(root):
        if TEST_NAME.search(path):
            continue
        # Siblings are searched in EVERY file including the edited one. They
        # usually live together: `Choice` and `DateTime` are both in click's
        # `types.py`, and skipping the file just edited would miss the exact
        # case this exists for.
        for symbol in _symbols(root, path):
            if (symbol.path, symbol.owner, symbol.name) in moved:
                continue        # the thing that changed is not its own sibling
            # A sibling shares a BASE, not merely a name. Two unrelated classes
            # both defining `convert` are not implementations of one interface,
            # and reporting them as such is the false positive this whole check
            # has to avoid.
            if (symbol.owner and symbol.name in methods
                    and set(symbol.bases) & interfaces):
                siblings.append(symbol)
        # Callers, though, are only news from elsewhere. A file referring to a
        # symbol it defines is not a dependency anyone needs warning about.
        if path not in here and wanted & _references(root, path):
            callers.append(path)

    # A class's line range contains its methods, so editing one method matched
    # both, and the message read "you changed Choice, Choice.convert" — the same
    # fact twice, less precisely. Trimmed for the report ONLY: the class still
    # had to be in `wanted` above, because `uses.py` calling `Choice()` is a
    # real dependency and dropping it earlier lost the caller entirely.
    owners = {s.owner for s in changed if s.owner}
    shown = [s for s in changed if s.owner or s.name not in owners]
    return Radius(changed=shown, siblings=siblings, callers=sorted(set(callers)))


def covering(root: Path, radius: Radius) -> list[str]:
    """Test files that look like they cover the dependents.

    Reuses `report`'s token rule rather than inventing a second notion of what
    "the test for this file" means, so the two cannot disagree about it.
    """
    from .report import _test_files, _tokens

    dependents = {s.path for s in radius.siblings} | set(radius.callers)
    if not dependents:
        return []
    wanted = {t for path in dependents for t in _tokens(path)}
    return sorted(p for p in _test_files(root) if wanted & _tokens(p))


def wording(radius: Radius, tests: list[str]) -> str:
    """One line for the report, or nothing at all."""
    if not radius:
        return ""
    changed = ", ".join(sorted({f"{s.owner}.{s.name}" if s.owner else s.name
                                for s in radius.changed})[:3])
    parts = []
    if radius.siblings:
        where = sorted({s.owner for s in radius.siblings})
        n = len(radius.siblings)
        shown = ", ".join(where[:3]) + (f" and {len(where) - 3} more" if len(where) > 3 else "")
        parts.append(f"{n} other implementation{'' if n == 1 else 's'} ({shown})")
    if radius.callers:
        n = len(radius.callers)
        parts.append(f"{n} file{'' if n == 1 else 's'} using it")
    said = f"you changed {changed}; {' and '.join(parts)}"
    if tests:
        return f"{said}. Closest cover: {', '.join(tests[:2])}"
    return f"{said}, and no test here covers them"
