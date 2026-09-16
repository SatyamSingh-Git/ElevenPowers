"""The architecture the code actually has, against the one the docs claim.

Design note: `docs/design/architecture-atlas.md`. The short version.

`CLAUDE.md` in this repository carries a standing rule to refresh
`architecture/` before finishing. It is forgotten, which is the ordinary fate of
soft policy: constraint violation rises **0% to 78% across four compaction
rounds**, and soft organisational policy decays about **8.3x faster** than hard
norms. So the map is not asked for. It is computed and compared.

**The borrow.** Murphy, Notkin & Sullivan, *Software Reflexion Models: Bridging
the Gap Between Source and High-Level Models* (FSE 1995, pp. 18-28) — an
engineer states a high-level model, a tool extracts one from the source, and the
comparison reports where they agree and where they differ. Thirty-one years old,
applied to 250,000 lines of NetBSD. What is added here: the high-level model is
not stated by hand, it is the architecture document the repository already
commits, and the comparison is attributed to the change that caused it.

**The second borrow.** Tan, Wagner & Treude, *Detecting Outdated Code Element
References in Software Repository Documentation* (EMSE 29(1):5, 2023,
arXiv:2212.01479) — over 3,000 GitHub projects, *"most projects contain at least
one outdated code element reference at some point in their history"*, detected
as references that survive in the documentation after the source is deleted.
That mechanism is used verbatim.

**Scoped to the task, deliberately.** Only drift *this change caused* is
reported. Standing drift is counted and named as a number. A first run that
emits two hundred findings is a first run that gets switched off, and this gate
has already blocked 75% of runs once on a signal nobody had measured.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

# Where an architecture document lives, in the order repositories put them.
# Discovered rather than configured: a setting nobody sets is a feature nobody
# gets, and the request was that everyone using the tool gets this.
MAP_DIRS = ("architecture", "docs/architecture")
MAP_FILES = ("ARCHITECTURE.md", "docs/ARCHITECTURE.md")

# Prose that *refers* to the code without being the map of it. The distinction
# is not cosmetic, and it was found by running this against its own repository:
# `core/radius.py` came back documented because the design note that proposed it
# mentions it. Being discussed in a design note is not being on the map, so
# prose cannot discharge divergence — but it is still documentation, so a stale
# reference in it is still a stale reference.
PROSE_DIRS = ("docs",)
PROSE_FILES = ("README.md",)
DOC_SUFFIX = (".md", ".html", ".rst", ".txt")


@dataclass(frozen=True)
class Drift:
    """Where the documents and the code disagree, in Murphy's three terms."""

    divergent: tuple[str, ...] = ()
    """Modules this task added that no document names. The map went stale."""
    absent: tuple[tuple[str, str], ...] = ()
    """(document, path) — the document still names a path this task removed."""
    documents: tuple[str, ...] = ()
    standing: int = 0
    """Modules undocumented before this task. Counted, never obligated."""

    def __bool__(self) -> bool:
        return bool(self.divergent or self.absent)


@dataclass
class Module:
    path: str
    imports: set[str] = field(default_factory=set)
    """Other modules in this repository that this one imports."""


def _found(root: Path, dirs: tuple[str, ...], files: tuple[str, ...]) -> list[str]:
    from .surface import _walk

    inside = tuple(d + "/" for d in dirs)
    return sorted(p for p in _walk(root)
                  if p.endswith(DOC_SUFFIX) and (p.startswith(inside) or p in files))


def maps(root: Path) -> list[str]:
    """The documents that are the architecture map, and so can discharge it.

    A repository with no dedicated map falls back to its README, which for a
    small project genuinely is the architecture document. A repository with
    neither gets nothing asked of it.
    """
    found = _found(root, MAP_DIRS, MAP_FILES)
    if found:
        return found
    return [p for p in _found(root, (), PROSE_FILES) if p == "README.md"]


def documents(root: Path) -> list[str]:
    """Every document that refers to the code, map or prose."""
    return sorted(set(maps(root)) | set(_found(root, PROSE_DIRS, PROSE_FILES)))


def _is_module(path: str) -> bool:
    from .surface import TEST_NAME

    return (path.endswith(".py") and not path.endswith("__init__.py")
            and not TEST_NAME.search(path))


def source_model(root: Path, limit: int = 1200) -> dict[str, Module]:
    """Modules, and the intra-repository imports between them.

    Third-party and standard-library imports are dropped on purpose. `import os`
    is not a fact about this repository's architecture, and a map that draws it
    is a map of Python rather than of the project.

    `limit` bounds it because this runs inside a 20-second hook: parsing costs
    about six milliseconds a module, so a repository past roughly this size
    would spend the agent's budget drawing a picture. Past the limit there is no
    model and the caller says nothing, which is the correct failure — a late
    architecture note is worse than none.
    """
    from .surface import _walk

    paths = [p for p in _walk(root) if _is_module(p)]
    if len(paths) > limit:
        return {}
    # Every suffix of the dotted path, because the import never spells the path
    # from the repository root: `src/app/store.py` is imported as `app.store`,
    # since `src/` is on sys.path rather than in the package name. Indexing only
    # the full path and the bare stem resolved neither.
    by_name: dict[str, str] = {}
    for path in paths:
        parts = path[:-3].split("/")
        for start in range(len(parts)):
            by_name.setdefault(".".join(parts[start:]), path)

    model = {p: Module(p) for p in paths}
    for path in paths:
        try:
            tree = ast.parse((root / path).read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError, ValueError):
            continue
        package = path.rsplit("/", 1)[0].replace("/", ".") if "/" in path else ""
        for node in ast.walk(tree):
            for name in _imported_names(node, package):
                target = _resolve(name, by_name)
                if target and target != path:
                    model[path].imports.add(target)
    return model


def _imported_names(node: ast.AST, package: str) -> list[str]:
    if isinstance(node, ast.Import):
        return [a.name for a in node.names]
    if isinstance(node, ast.ImportFrom):
        if node.level:
            # `from .radius import x` in core/atlas.py means core.radius. One
            # level is the containing package, each further level strips a part.
            parts = package.split(".") if package else []
            base = ".".join(parts[:len(parts) - node.level + 1])
            head = f"{base}.{node.module}" if node.module else base
        else:
            head = node.module or ""
        if not head:
            return []
        # `from core.radius import compute` names the module; `from core import
        # radius` names it through the imported symbol. Offer both.
        return [head] + [f"{head}.{a.name}" for a in node.names]
    return []


def _resolve(dotted: str, by_name: dict[str, str]) -> str:
    while dotted:
        if dotted in by_name:
            return by_name[dotted]
        dotted = dotted.rpartition(".")[0]
    return ""


def _names(text: str, path: str) -> bool:
    """Does a document name this module?

    The full path, or the bare filename, which is how a document written before
    a `src/` layout still refers to the same module. Not the bare stem: `atlas`
    in prose is a word, and this project has already paid four rounds of false
    positives for matching prose.
    """
    return path in text or path.rsplit("/", 1)[-1] in text


def _doc_text(root: Path, docs: list[str]) -> dict[str, str]:
    out = {}
    for doc in docs:
        try:
            out[doc] = (root / doc).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return out


def reflexion(root: Path, added: list[str], removed: list[str]) -> Drift:
    """Compare the documents against the code, for what this task changed.

    A repository with no architecture document gets an empty `Drift` and no
    complaint. `core/surface.py` exists because an obligation nothing can
    discharge is a design error rather than a finding, and the same rule applies
    here: there is nothing to update if there is nothing to update.
    """
    docs = documents(root)
    if not docs:
        return Drift()
    text = _doc_text(root, docs)
    drawn = "\n".join(_doc_text(root, maps(root)).values())

    divergent = tuple(p for p in sorted(set(added))
                      if _is_module(p) and not _names(drawn, p))

    # The outdated-reference mechanism, restricted to paths this task removed.
    # Restricting it is what makes it exact: a path that never existed is never
    # examined, so there is no way to mistake an example in a fenced block for a
    # claim about the repository.
    absent = tuple((doc, path) for path in sorted(set(removed))
                   for doc, body in sorted(text.items())
                   if path and path in body)

    from .surface import _walk

    standing = sum(1 for p in _walk(root)
                   if _is_module(p) and p not in set(added) and not _names(drawn, p))
    return Drift(divergent, absent, tuple(docs), standing)


def neighbourhood(root: Path, path: str, model: dict[str, Module] | None = None) -> str:
    """What sits around a file, for the agent about to edit it.

    This is the half of the request that computing a true map does not satisfy:
    the map has to reach the agent at the moment it is deciding something, and
    the moment before an edit is the only moment the information can change the
    edit.
    """
    if not _is_module(path):
        return ""
    model = source_model(root) if model is None else model
    if path not in model:
        return ""
    out = sorted(model[path].imports)
    into = sorted(p for p, m in model.items() if path in m.imports)
    if not out and not into:
        return ""
    parts = []
    if into:
        parts.append(f"imported by {', '.join(into[:4])}"
                     + (f" (+{len(into) - 4} more)" if len(into) > 4 else ""))
    if out:
        parts.append(f"it imports {', '.join(out[:4])}"
                     + (f" (+{len(out) - 4} more)" if len(out) > 4 else ""))
    described = [d for d, body in _doc_text(root, documents(root)).items() if _names(body, path)]
    said = f"{path}: {'; '.join(parts)}"
    return f"{said}. Described in {described[0]}" if described else said


RENAME = re.compile(r"^R\d*$")


def since(root: Path, base: str) -> tuple[list[str], list[str]]:
    """Files this task added and removed, from git.

    A rename is both: the old path is gone, so a document naming it is now
    stale, and the new path is a module no map has drawn yet. Treating a rename
    as neither is how the commonest kind of drift goes unnoticed.
    """
    import subprocess

    if not base:
        return [], []
    try:
        done = subprocess.run(["git", "diff", "--name-status", base], cwd=root,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60)
        extra = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"],
                               cwd=root, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return [], []
    if done.returncode != 0:
        return [], []

    added, removed = [], []
    for line in done.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        code = parts[0]
        if code == "A":
            added.append(parts[1])
        elif code == "D":
            removed.append(parts[1])
        elif RENAME.match(code) and len(parts) >= 3:
            removed.append(parts[1])
            added.append(parts[2])
    if extra.returncode == 0:
        added += [p for p in extra.stdout.split() if p]
    return sorted(set(added)), sorted(set(removed))


def wording(drift: Drift) -> list[str]:
    """The report lines, or none at all."""
    if not drift:
        return []
    said = []
    if drift.divergent:
        where = drift.documents[0] if drift.documents else "the architecture map"
        shown = ", ".join(drift.divergent[:3])
        more = f" (+{len(drift.divergent) - 3} more)" if len(drift.divergent) > 3 else ""
        said.append(f"architecture: {shown}{more} added, and {where} does not name "
                    f"{'them' if len(drift.divergent) > 1 else 'it'}")
    for doc, path in drift.absent[:3]:
        said.append(f"docs: {doc} still names {path}, which this change removed")
    if len(drift.absent) > 3:
        said.append(f"docs: {len(drift.absent) - 3} more stale reference(s)")
    if drift.standing:
        said.append(f"({drift.standing} module(s) were already undrawn before this change)")
    return said


def initial_map(root: Path) -> str:
    """A first `ARCHITECTURE.md`, generated from the code.

    Most repositories have no architecture document, so there is nothing for the
    reflexion to compare against and the feature is silent for them. Writing the
    first one from the source model is what makes the check available at all —
    and it is true on the day it is written, because the code produced it.

    Deliberately a skeleton a human is expected to rewrite. Following matklad's
    `ARCHITECTURE.md` convention (2021), it names modules; unlike his advice it
    names them precisely, which is affordable here only because staleness is now
    detected rather than avoided.
    """
    model = source_model(root)
    by_dir: dict[str, list[str]] = {}
    for path in sorted(model):
        by_dir.setdefault(path.rsplit("/", 1)[0] if "/" in path else ".", []).append(path)

    lines = [f"# Architecture: {root.name}", "",
             "Generated from the source by ElevenPowers, and kept honest by it.",
             "Rewrite the prose; keep the module names, which is what the drift",
             "check compares against.", ""]
    for folder, paths in sorted(by_dir.items()):
        lines.append(f"## `{folder}`")
        lines.append("")
        for path in paths:
            into = sorted(p for p, m in model.items() if path in m.imports)
            used = f" — used by {', '.join(f'`{p}`' for p in into[:3])}" if into else ""
            lines.append(f"- `{path}`{used}")
        lines.append("")
    return "\n".join(lines)
