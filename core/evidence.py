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
import time
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
    """The working tree as version control saw it, recorded as provenance.

    It used to be a tie-breaker: when modification times moved but git reported
    no change, the evidence was kept. That was the unsound step. A fingerprint
    over file contents needs no tie-breaker — identical bytes hash identically,
    so a formatter rewriting a file no longer stales anything, which is the only
    thing the tie-breaker was there to prevent.
    """
    counted: bool = False
    """Whether this record comes from a parser that counts tests and looked.

    Zero tests then means zero tests ran. Without it, a wrapper whose output
    nobody can count is indistinguishable from `echo pytest`, and refusing both
    would block agents whose projects run tests through `make`.
    """
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
        return Freshness.STALE

    @property
    def ran_tests(self) -> bool:
        """Whether a run that counts tests saw any test execute.

        `echo pytest` exits zero and contains a runner's name. The record it
        produced counted no tests and satisfied "the related test suite passes"
        anyway, because a completed process and an executed test were the same
        thing here. They are four separate facts: the command was recognised,
        the process finished, tests ran, and the required ones passed.
        """
        return not self.counted or (self.passed + self.failed) > 0

    def __post_init__(self) -> None:
        """Strip credentials from the text this record carries.

        `Ledger.saw_output` was made to scrub, and this was missed: `detail`
        holds a tail of the same output, and an audit found a token surviving
        in serialized evidence after being removed from the output sample. One
        redacted copy and one unredacted copy of the same bytes is not a
        redaction. Done at construction rather than at `to_dict`, so the record
        never holds it in memory either.
        """
        from .redact import scrub

        if self.detail:
            self.detail = scrub(self.detail)
        if self.command:
            self.command = scrub(self.command)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["kind"] = self.kind.value
        d["result"] = self.result.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Evidence":
        return cls(**{**d, "kind": Kind(d["kind"]), "result": Result(d["result"])})


# A file modified this recently is re-read whatever the cache holds, because
# this is the window where size and modification time cannot resolve an edit —
# and it is the window an agent's edits land in. Git calls the same rule
# racily-clean and applies it for the same reason.
RACY_NS = 2_000_000_000

_DIGESTS: dict[tuple[str, str], tuple[int, int, str]] = {}


def _digest(root: Path, rel: str) -> str:
    """One file's content hash, with stat as a cache key rather than the answer.

    This used to be size and modification time alone, on the argument that a
    file rewritten with identical bytes would merely read as stale and cost one
    redundant re-run. The error was in the other direction: **a rewrite that
    keeps the length and lands inside the filesystem's timestamp resolution is
    invisible.** Rewriting a two-line lock file was invisible to stat in 220 of
    300 attempts on the machine this was measured on, so evidence surviving a
    real edit was the common case rather than a race.
    """
    path = root / rel
    try:
        stat = path.stat()
    except OSError:
        return "missing"
    hit = _DIGESTS.get((str(root), rel))
    if (hit and (hit[0], hit[1]) == (stat.st_size, stat.st_mtime_ns)
            and time.time_ns() - stat.st_mtime_ns > RACY_NS):
        return hit[2]
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        return "missing"
    _DIGESTS[(str(root), rel)] = (stat.st_size, stat.st_mtime_ns, digest)
    return digest


def tree_hash(root: Path, paths: Iterable[str]) -> str:
    """A signature over the contents of a set of repository-relative paths.

    Measured on this repository: 6ms to hash 59 files against 1ms to stat them.
    The cache is what keeps that affordable at scale, since a status check hashes
    the tree once per evidence record, and an uncached full pass on a large
    repository would run into the host's 20-second hook timeout rather than
    merely being slow.
    """
    h = hashlib.sha256()
    for rel in sorted(paths):
        h.update(rel.encode())
        h.update(f"\0{_digest(root, rel)}\0".encode())
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
                                  text=True, encoding="utf-8", errors="replace", timeout=10)
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
