"""Evidence records and freshness.

An evidence record is a fact about the repository produced by a command the
agent ran. It is bound to the content of the files it observed, so that a later
edit to any of them makes the record stale. This is the same dependency
relationship a build system tracks between an object file and its sources.
"""

from __future__ import annotations

import fnmatch
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
    execution: str = "complete"
    coverage_issues: list[str] = field(default_factory=list)
    scope: str = ""
    """Where `observed` came from, when it was a scan rather than a fixed list.

    `source` means every source file in the tree. Such a record has to be
    checked against the tree as it is now, not against the list stored inside
    it: a file that did not exist when the suite ran cannot be in that list, so
    a stored list can never notice one being added. A new failing test is the
    ordinary case, and it stales nothing at all.
    """

    def freshness(self, root: Path) -> Freshness:
        if self.coverage_issues:
            return Freshness.STALE
        if self.scope == "source":
            scan, digest = source_snapshot(root)
            if not scan.complete:
                self.coverage_issues = scan.issues
                return Freshness.STALE
            if digest == self.tree:
                return Freshness.FRESH
            if any(not (root / p).exists() for p in self.observed):
                return Freshness.GONE
            return Freshness.STALE
        if not self.observed:
            return Freshness.FRESH
        current = self.observed
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


def _git_sources(root: Path) -> list[str] | None:
    """Let Git interpret ignore rules, including negation and nested rules."""
    def git(*args):
        return subprocess.run(
            ["git", "-c", f"safe.directory={root.as_posix()}", *args], cwd=root,
            capture_output=True, timeout=10,
        )
    try:
        top = git("rev-parse", "--show-toplevel")
        if top.returncode or Path(os.fsdecode(top.stdout).strip()).resolve() != root.resolve():
            return None
        found = git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
        if found.returncode:
            return None
    except (OSError, subprocess.SubprocessError):
        return None
    return sorted(set(os.fsdecode(p) for p in found.stdout.split(b"\0") if p))


@dataclass
class SourceScan:
    files: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    bytes: int = 0

    @property
    def complete(self) -> bool:
        return not self.issues


def scan_sources(root: Path, limit: int | None = None, max_bytes: int | None = None) -> SourceScan:
    """Bounded source selection; failures and omitted inputs remain explicit."""
    from .config import load
    scan = SourceScan()
    policy = load(root).scan
    if not isinstance(policy, dict):
        scan.issues.append("invalid scan configuration: expected an object")
        policy = {}
    def budget(value, default, name):
        if type(value) is not int or value <= 0:
            scan.issues.append(f"invalid scan {name}: expected a positive integer")
            return default
        return value
    limit = budget(limit if limit is not None else policy.get("max_files", 20000), 20000, "max_files")
    max_bytes = budget(max_bytes if max_bytes is not None else policy.get("max_bytes", 67108864), 67108864, "max_bytes")
    excludes = policy.get("exclude", [])
    if not isinstance(excludes, list) or any(not isinstance(p, str) or not p for p in excludes):
        scan.issues.append("invalid scan exclude: expected a list of nonempty relative patterns")
        excludes = []
    def excluded(rel):
        return any(fnmatch.fnmatchcase(rel, p.rstrip("/") + "/*" if p.endswith("/") else p)
                   for p in excludes)
    root = root.resolve()
    candidates = _git_sources(root)
    if candidates is None:
        if (root / ".git").exists():
            scan.issues.append("Git enumeration unavailable; filesystem fallback cannot verify ignore rules")
        candidates = []
        def walk_error(error):
            scan.issues.append(f"unreadable directory: {error.filename}")
        for dirpath, dirnames, filenames in os.walk(root, onerror=walk_error):
            for d in dirnames:
                if (Path(dirpath) / d).is_symlink():
                    scan.issues.append(f"symlink directory excluded: {Path(dirpath, d).relative_to(root)}")
            dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_DIRS
                                 and not (Path(dirpath) / d).is_symlink()
                                 and not excluded(str(Path(dirpath, d).relative_to(root)).replace("\\", "/") + "/")
                                 and not (Path(dirpath) / d / ".git").exists())
            candidates.extend(str(Path(dirpath, name).relative_to(root)).replace("\\", "/")
                              for name in sorted(filenames))
    for rel in sorted(candidates):
        if excluded(rel):
            continue
        path = Path(rel)
        if path.suffix not in SOURCE_SUFFIXES and path.name not in DEPENDENCY_FILES:
            continue
        if any(part in {".git", ".elevenpowers"} for part in path.parts):
            continue
        if any((root / parent / ".git").exists() for parent in path.parents if str(parent) != "."):
            continue
        full = root / path
        if path.is_absolute() or ".." in path.parts or full.is_symlink():
            scan.issues.append(f"unsafe or symlink input excluded: {rel}")
            continue
        if any((root / parent).is_symlink() for parent in path.parents if str(parent) != "."):
            scan.issues.append(f"symlink parent excluded: {rel}")
            continue
        try:
            if not full.is_file():
                continue
            size = full.stat().st_size
        except OSError:
            scan.issues.append(f"unreadable input: {rel}")
            continue
        if len(scan.files) >= limit:
            scan.issues.append(f"file limit {limit} exceeded; source coverage is incomplete")
            break
        if scan.bytes + size > max_bytes:
            scan.issues.append(f"byte limit {max_bytes} exceeded at {rel}; source coverage is incomplete")
            break
        scan.files.append(rel)
        scan.bytes += size
    return scan


def source_files(root: Path, limit: int | None = None) -> list[str]:
    """Compatibility view for advisory callers; evidence uses scan_sources."""
    return scan_sources(root, limit=limit).files


def source_snapshot(root: Path) -> tuple[SourceScan, str]:
    """Bind the selected inputs and any coverage failures to the same receipt."""
    scan = scan_sources(root)
    digest = hashlib.sha256()
    for rel in scan.files:
        value = _digest(root, rel)
        if value == "missing":
            scan.issues.append(f"unreadable or disappeared input: {rel}")
        digest.update(rel.encode())
        digest.update(f"\0{value}\0".encode())
    return scan, digest.hexdigest()[:16]
