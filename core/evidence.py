"""Evidence records and freshness.

An evidence record is a fact about the repository produced by a command the
agent ran. It is bound to the content of the files it observed, so that a later
edit to any of them makes the record stale. This is the same dependency
relationship a build system tracks between an object file and its sources.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Iterable


class Kind(str, Enum):
    TEST = "test"
    SUITE = "test_suite"
    BUILD = "build"
    TYPECHECK = "typecheck"
    LINT = "lint"
    RUNTIME = "runtime"
    BENCHMARK = "benchmark"
    STABILITY = "stability"
    BROWSER = "browser"
    SCANNER = "scanner"
    DIFF = "diff"


class Result(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


class Freshness(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    GONE = "gone"


@dataclass
class Evidence:
    kind: Kind
    identity: str
    result: Result
    observed: list[str]
    tree: str
    command: str = ""
    detail: str = ""
    passed: int = 0
    failed: int = 0
    at: float = 0.0
    run: str = ""
    runs: int = 0
    vcs: str = ""
    scope: str = ""
    """Where `observed` came from, when it was a scan rather than a fixed list.

    `source` means every source file in the tree. Such a record has to be
    checked against the tree as it is now, not against the list stored inside
    it: a file that did not exist when the suite ran cannot be in that list, so
    a stored list can never notice one being added. A new failing test is the
    ordinary case, and it stales nothing at all.
    """

    def freshness(self, root: Path) -> Freshness:
        if not self.observed:
            # Depends on no files, so no edit can invalidate it. A stated
            # blocker is the case that matters: it is about the world, not
            # about the code.
            return Freshness.FRESH
        current = source_files(root) if self.scope == "source" else self.observed
        if tree_hash(root, current) == self.tree:
            return Freshness.FRESH
        if any(not (root / p).exists() for p in self.observed):
            return Freshness.GONE
        # Modification times moved. Git compares content rather than timestamps,
        # so an unchanged working-tree state means a formatter or a checkout
        # rewrote bytes that were already there, and the evidence still holds.
        if self.vcs and self.vcs == vcs_state(root):
            return Freshness.FRESH
        return Freshness.STALE

    def to_dict(self) -> dict:
        d = asdict(self)
        d["kind"] = self.kind.value
        d["result"] = self.result.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Evidence":
        return cls(**{**d, "kind": Kind(d["kind"]), "result": Result(d["result"])})


def tree_hash(root: Path, paths: Iterable[str]) -> str:
    """A signature over a set of repository-relative paths.

    Size and modification time rather than contents. Reading every file was
    measured at about 6 seconds on an 8,000 file repository, which would be paid
    on every test run; stat brings the same work to roughly 200 milliseconds.

    The trade is that a file rewritten with identical bytes changes its
    modification time and so reads as stale. That costs one redundant re-run and
    is self-correcting, where the slow version would have made the tool unusable
    on any large codebase. Build systems make the same trade for the same
    reason.
    """
    h = hashlib.sha256()
    for rel in sorted(paths):
        h.update(rel.encode())
        try:
            stat = (root / rel).stat()
            h.update(f"\0{stat.st_size}\0{stat.st_mtime_ns}\0".encode())
        except OSError:
            h.update(b"\0missing\0")
    return h.hexdigest()[:16]


def vcs_state(root: Path) -> str:
    """A fingerprint of the working tree's content as version control sees it.

    Git compares file content, using timestamps only as a cache, so two calls
    returning the same value mean no file content changed between them. That is
    the distinction stat alone cannot make and the reason a formatter rewriting
    identical bytes should not invalidate a test result. Returns an empty string
    outside a repository, where the caller falls back to timestamps.

    A porcelain status alone is not that fingerprint. It names which files
    differ from HEAD and not how they differ, so two different edits to one
    already-modified file share a status line — and evidence recorded against
    the first survived the second, which is the one thing this layer promises
    never to happen. The diff carries content for tracked files. Untracked ones
    are read directly, because a test file the agent wrote a minute ago is
    untracked and is exactly what changes next.
    """
    def git(*args: str) -> str | None:
        try:
            done = subprocess.run(["git", *args], cwd=root, capture_output=True,
                                  text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return None
        return done.stdout if done.returncode == 0 else None

    top = git("rev-parse", "--show-toplevel")
    if top is None or Path(top.strip()).resolve() != root.resolve():
        return ""
    head = git("rev-parse", "HEAD") or ""
    status = git("status", "--porcelain", "--untracked-files=all")
    changes = git("diff", "HEAD")
    if status is None or changes is None:
        return ""
    h = hashlib.sha256((head + "\n--\n" + status + "\n--\n" + changes).encode())
    for line in status.splitlines():
        if not line.startswith("??"):
            continue
        path = root / line[3:].strip().strip('"')
        if path.is_file():
            h.update(path.read_bytes())
    return h.hexdigest()[:16]


IGNORED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", "dist", "build", ".next",
    ".tox", "target", ".gradle", ".idea", ".elevenpowers",
}

SOURCE_SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs", ".rb",
    ".java", ".kt", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".php",
    ".scala", ".ex", ".exs", ".css", ".scss", ".sql", ".json", ".yaml", ".yml",
    ".toml",
}

# What the code depends on that is not code. A dependency upgrade changes
# behaviour exactly as an edit does, and a suite that passed before one has no
# claim on the repository after it. Named rather than matched by suffix,
# because `.lock` and `.txt` and `.mod` say nothing on their own.
DEPENDENCY_FILES = {
    "requirements.txt", "requirements-dev.txt", "dev-requirements.txt",
    "constraints.txt", "Pipfile", "Pipfile.lock", "poetry.lock", "uv.lock",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "npm-shrinkwrap.json",
    "Cargo.lock", "go.mod", "go.sum", "Gemfile", "Gemfile.lock",
    "composer.lock", "mix.lock", "gradle.lockfile",
}


def source_files(root: Path, limit: int = 20000) -> list[str]:
    """Every tracked-looking source file and dependency manifest, sorted.

    Used as the observed set for coarse invalidation: any source edit stales
    everything. Pessimistic on purpose. Static import-closure narrowing is the
    documented next step, gated on measuring that this is too coarse to live
    with (P4).

    It still cannot see a package installed without touching a manifest. That
    is the part of R2 left open, and it is stated rather than papered over.
    """
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        for name in filenames:
            if Path(name).suffix in SOURCE_SUFFIXES or name in DEPENDENCY_FILES:
                out.append(str(Path(dirpath, name).relative_to(root)).replace("\\", "/"))
                if len(out) >= limit:
                    return sorted(out)
    return sorted(out)
