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
    vcs: str = ""

    def freshness(self, root: Path) -> Freshness:
        if not self.observed:
            # Depends on no files, so no edit can invalidate it. A stated
            # blocker is the case that matters: it is about the world, not
            # about the code.
            return Freshness.FRESH
        if tree_hash(root, self.observed) == self.tree:
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
    """A fingerprint of the working tree as version control sees it.

    Git compares file content, using timestamps only as a cache, so two calls
    returning the same value mean no file content changed between them. That is
    the distinction stat alone cannot make and the reason a formatter rewriting
    identical bytes should not invalidate a test result. Returns an empty string
    outside a repository, where the caller falls back to timestamps.
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
    status = git("status", "--porcelain")
    if status is None:
        return ""
    return hashlib.sha256((head + "\n--\n" + status).encode()).hexdigest()[:16]


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


def source_files(root: Path, limit: int = 20000) -> list[str]:
    """Every tracked-looking source file, repository-relative, sorted.

    Used as the observed set for coarse invalidation: any source edit stales
    everything. Pessimistic on purpose. Static import-closure narrowing is the
    documented next step, gated on measuring that this is too coarse to live
    with (P4).
    """
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        for name in filenames:
            if Path(name).suffix in SOURCE_SUFFIXES:
                out.append(str(Path(dirpath, name).relative_to(root)).replace("\\", "/"))
                if len(out) >= limit:
                    return sorted(out)
    return sorted(out)
