"""Evidence records and freshness.

An evidence record is a fact about the repository produced by a command the
agent ran. It is bound to the content of the files it observed, so that a later
edit to any of them makes the record stale. This is the same dependency
relationship a build system tracks between an object file and its sources.
"""

from __future__ import annotations

import hashlib
import os
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

    def freshness(self, root: Path) -> Freshness:
        if any(not (root / p).exists() for p in self.observed):
            return Freshness.GONE
        return Freshness.FRESH if tree_hash(root, self.observed) == self.tree else Freshness.STALE

    def to_dict(self) -> dict:
        d = asdict(self)
        d["kind"] = self.kind.value
        d["result"] = self.result.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Evidence":
        return cls(**{**d, "kind": Kind(d["kind"]), "result": Result(d["result"])})


def tree_hash(root: Path, paths: Iterable[str]) -> str:
    """Content hash over a set of repository-relative paths.

    Paths are sorted so the hash is order-independent, and each contributes its
    own path as well as its bytes so that renames register as a change.
    """
    h = hashlib.sha256()
    for rel in sorted(paths):
        h.update(rel.encode())
        h.update(b"\0")
        try:
            h.update((root / rel).read_bytes())
        except OSError:
            h.update(b"<unreadable>")
        h.update(b"\0")
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
