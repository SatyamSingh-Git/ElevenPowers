"""Evidence records and freshness.

An evidence record is a fact about the repository produced by a command the
agent ran. It is bound to the content of the files it observed, so that a later
edit to any of them makes the record stale. This is the same dependency
relationship a build system tracks between an object file and its sources.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

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


_FRESHNESS_VIEW = ContextVar('freshness_report_view', default=None)


@contextmanager
def freshness_view(root: Path, *, deadline=None):
    """Fresh source and explicit inputs, scoped to one bounded operation."""
    resolved = root.resolve()
    digests = {}
    parent = _FRESHNESS_VIEW.set(None)
    try:
        snapshot = source_snapshot(resolved, fresh=True, deadline=deadline, digests=digests)
    finally:
        _FRESHNESS_VIEW.reset(parent)
    view = _FreshView(resolved, snapshot, digests, deadline)
    token = _FRESHNESS_VIEW.set(view)
    try:
        yield snapshot
    finally:
        _FRESHNESS_VIEW.reset(token)


class _FreshView:
    def __init__(self, root, snapshot, digests, deadline):
        from .config import load
        self.root, self.snapshot, self.digests, self.deadline = root, snapshot, digests, deadline
        policy = load(root).scan
        policy = policy if isinstance(policy, dict) else {}
        self.max_files = policy.get('max_files', 20000)
        self.max_bytes = policy.get('max_bytes', 268435456)
        if type(self.max_files) is not int or self.max_files <= 0:
            self.max_files = 20000
        if type(self.max_bytes) is not int or self.max_bytes <= 0:
            self.max_bytes = 268435456
        self.bytes = snapshot[0].bytes

    def digest(self, rel):
        if rel in self.digests:
            return self.digests[rel]
        scan = self.snapshot[0]
        path = Path(rel)
        full = self.root / path
        try:
            if (path.is_absolute() or '..' in path.parts
                    or any(p in {'.git', '.elevenpowers'} for p in path.parts)
                    or any((self.root / p).is_symlink() for p in (path, *path.parents))
                    or any((self.root / p / '.git').exists() for p in path.parents if str(p) != '.')
                    or not full.resolve().is_relative_to(self.root)):
                raise ValueError('unsafe explicit input')
            if len(self.digests) >= self.max_files:
                raise ValueError('explicit input file limit exceeded')
            size = full.stat().st_size
            if not full.is_file() or self.bytes + size > self.max_bytes:
                raise ValueError('explicit input byte limit exceeded or input is not a file')
            digest = hashlib.sha256()
            with full.open('rb') as stream:
                while True:
                    if self.deadline is not None and time.monotonic() >= self.deadline:
                        raise TimeoutError('report deadline reached reading explicit input')
                    chunk = stream.read(min(1024 * 1024, self.max_bytes - self.bytes + 1))
                    self.bytes += len(chunk)
                    if self.bytes > self.max_bytes:
                        raise ValueError('explicit input byte limit exceeded')
                    if not chunk:
                        break
                    digest.update(chunk)
            value = digest.hexdigest()[:16]
        except (OSError, ValueError) as error:
            scan.issues.append(f'{error.__class__.__name__}: explicit input coverage incomplete at {rel}')
            value = 'missing'
        self.digests[rel] = value
        return value


def freshness_deadline(root):
    view = _FRESHNESS_VIEW.get()
    return view.deadline if view is not None and view.root == root.resolve() else None


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
    declaration: str = ""
    declared_command: str = ""
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
        if self.declaration:
            from .config import load
            from .redact import scrub
            if scrub(load(root).command_for(self.declaration)) != (self.declared_command or self.command):
                return Freshness.STALE
        if self.coverage_issues:
            return Freshness.STALE
        if self.scope == "source":
            view = _FRESHNESS_VIEW.get()
            scan, digest = view.snapshot if view is not None and view.root == root.resolve() else source_snapshot(root)
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
        if self.declared_command:
            self.declared_command = scrub(self.declared_command)

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
    view = _FRESHNESS_VIEW.get()
    if view is not None and view.root == root.resolve():
        return view.digest(rel)
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


def tree_hash(root: Path, paths: Iterable[str], *, fresh: bool = False) -> str:
    """A signature over the contents of a set of repository-relative paths.

    Measured on this repository: 6ms to hash 59 files against 1ms to stat them.
    The cache is what keeps that affordable at scale, since a status check hashes
    the tree once per evidence record, and an uncached full pass on a large
    repository would run into the host's 20-second hook timeout rather than
    merely being slow.
    """
    h = hashlib.sha256()
    for rel in sorted(paths):
        if fresh:
            _DIGESTS.pop((str(root), rel), None)
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
    ".py", ".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs", ".rb",
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


def _git_sources(root: Path, *, deadline=None) -> list[str] | None:
    """Let Git interpret ignore rules, including negation and nested rules."""
    repository = next((p for p in (root, *root.parents) if (p / ".git").exists()), None)
    if repository is None:
        return None
    def git(*args):
        allowance = 10 if deadline is None else min(10, deadline - time.monotonic())
        if allowance <= 0:
            raise TimeoutError('source enumeration deadline reached')
        return subprocess.run(
            ["git", "-c", f"safe.directory={repository.as_posix()}",
             "-c", "core.fsmonitor=false", *args], cwd=root,
            capture_output=True, timeout=allowance,
        )
    try:
        top = git("rev-parse", "--show-toplevel")
        if top.returncode:
            raise OSError("Git repository discovery failed")
        # Ignored scratch projects are independent filesystem scopes.
        if repository != root and git("check-ignore", "-q", ".").returncode == 0:
            return None
        found = git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
        if found.returncode:
            raise OSError("Git file enumeration failed")
    except (OSError, subprocess.SubprocessError) as error:
        raise OSError("Git enumeration unavailable") from error
    return sorted(set(os.fsdecode(p) for p in found.stdout.split(b"\0") if p))


@dataclass
class SourceScan:
    files: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    bytes: int = 0

    @property
    def complete(self) -> bool:
        return not self.issues


_SCAN_POLICY_DEFAULT = object()


def scan_sources(root: Path, limit: int | None = None, max_bytes: int | None = None,
                 *, deadline: float | None = None, policy=_SCAN_POLICY_DEFAULT) -> SourceScan:
    """Bounded source selection; failures and omitted inputs remain explicit."""
    from .config import load
    scan = SourceScan()
    def expired():
        if deadline is not None and time.monotonic() >= deadline:
            scan.issues.append("verification deadline reached; source coverage is incomplete")
            return True
        return False
    if expired():
        return scan
    if policy is _SCAN_POLICY_DEFAULT:
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
    max_bytes = budget(max_bytes if max_bytes is not None else policy.get("max_bytes", 268435456), 268435456, "max_bytes")
    excludes = policy.get("exclude", [])
    if not isinstance(excludes, list) or any(not isinstance(p, str) or not p for p in excludes):
        scan.issues.append("invalid scan exclude: expected a list of nonempty relative patterns")
        excludes = []
    def excluded(rel):
        return any(fnmatch.fnmatchcase(rel, p.rstrip("/") + "/*" if p.endswith("/") else p)
                   for p in excludes)
    root = root.resolve()
    try:
        candidates = _git_sources(root, deadline=deadline) if deadline is not None else _git_sources(root)
    except OSError:
        scan.issues.append("Git enumeration unavailable; filesystem fallback cannot verify ignore rules")
        candidates = None
    if candidates is None:
        if (root / ".git").exists():
            scan.issues.append("Git enumeration unavailable; filesystem fallback cannot verify ignore rules")
        candidates = []
        def walk_error(error):
            scan.issues.append(f"unreadable directory: {error.filename}")
        for dirpath, dirnames, filenames in os.walk(root, onerror=walk_error):
            if expired():
                break
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
        if expired():
            break
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


def source_snapshot(root: Path, *, fresh: bool = False,
                    deadline: float | None = None, digests=None) -> tuple[SourceScan, str]:
    """Bind the selected inputs and any coverage failures to the same receipt."""
    scan = scan_sources(root, deadline=deadline) if deadline is not None else scan_sources(root)
    digest = hashlib.sha256()
    for rel in scan.files:
        if deadline is not None and time.monotonic() >= deadline:
            scan.issues.append("verification deadline reached while hashing inputs")
            break
        if fresh:
            _DIGESTS.pop((str(root), rel), None)
        value = _digest(root, rel)
        if digests is not None:
            digests[rel] = value
        if value == "missing":
            scan.issues.append(f"unreadable or disappeared input: {rel}")
        digest.update(rel.encode())
        digest.update(f"\0{value}\0".encode())
    return scan, digest.hexdigest()[:16]
