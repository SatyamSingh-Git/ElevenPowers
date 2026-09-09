"""Turn test-runner and compiler output into evidence records.

Parsing rather than asking. The agent runs these commands anyway; the runtime
reads the output it already produces. Nothing here prompts a model.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from .evidence import Evidence, Kind, Result, source_files, tree_hash

PYTEST_TAIL = re.compile(
    r"^=+ (?:(?P<failed>\d+) failed)?,? ?(?:(?P<passed>\d+) passed)?"
    r".*?(?:(?P<errors>\d+) errors?)?.*?=+$",
    re.MULTILINE,
)
PYTEST_NODE = re.compile(r"^(?P<status>PASSED|FAILED|ERROR)\s+(?P<node>\S+::\S+)", re.MULTILINE)
PYTEST_SHORT = re.compile(r"^(?P<node>\S+::\S+)\s+(?P<status>PASSED|FAILED|ERROR)", re.MULTILINE)

JEST_TESTS = re.compile(r"^Tests:\s+(?P<body>.+)$", re.MULTILINE)
JEST_SUITES = re.compile(r"^Test Suites:\s+(?P<body>.+)$", re.MULTILINE)
VITEST_TESTS = re.compile(r"Tests\s+(?P<body>.+?)$", re.MULTILINE)

TSC_ERROR = re.compile(r"^(?P<file>[^\s(]+)\((?P<line>\d+),\d+\): error TS\d+", re.MULTILINE)
TSC_COUNT = re.compile(r"Found (?P<n>\d+) errors?", re.MULTILINE)

GO_RESULT = re.compile(r"^(?P<status>ok|FAIL|---\s+FAIL)\s+(?P<pkg>\S+)", re.MULTILINE)
CARGO_RESULT = re.compile(
    r"test result:\s+(?P<status>ok|FAILED)\.\s+(?P<passed>\d+) passed;\s+(?P<failed>\d+) failed",
    re.MULTILINE,
)


def _counts(body: str) -> tuple[int, int]:
    passed = failed = 0
    for n, word in re.findall(r"(\d+)\s+(passed|failed)", body):
        if word == "passed":
            passed = int(n)
        else:
            failed = int(n)
    return passed, failed


def parse(command: str, output: str, exit_code: int, root: Path) -> list[Evidence]:
    """Evidence implied by one command and its output, or an empty list."""
    cmd = command.strip()
    lowered = cmd.lower()

    if "pytest" in lowered or re.search(r"\bpython -m pytest\b", lowered):
        return _pytest(cmd, output, exit_code, root)
    if "vitest" in lowered:
        return _js(cmd, output, exit_code, root, VITEST_TESTS)
    if "jest" in lowered:
        return _js(cmd, output, exit_code, root, JEST_TESTS)
    if "tsc" in lowered:
        return _tsc(cmd, output, exit_code, root)
    if re.search(r"\bgo test\b", lowered):
        return _go(cmd, output, exit_code, root)
    if re.search(r"\bcargo (test|nextest)\b", lowered):
        return _cargo(cmd, output, exit_code, root)
    if re.search(r"\b(npm|pnpm|yarn) run (build|compile)\b", lowered) or re.search(r"\bcargo build\b", lowered):
        return [_record(Kind.BUILD, _scope(cmd), exit_code, cmd, root, output)]
    if re.search(r"\b(ruff|eslint|flake8|clippy)\b", lowered):
        return [_record(Kind.LINT, _scope(cmd), exit_code, cmd, root, output)]
    if re.search(r"\b(mypy|pyright)\b", lowered):
        return [_record(Kind.TYPECHECK, _scope(cmd), exit_code, cmd, root, output)]
    return []


def _scope(command: str) -> str:
    """A stable identity for a command-level record: the target it names."""
    parts = [p for p in command.split() if not p.startswith("-")]
    tail = [p for p in parts[1:] if "/" in p or "." in p or "::" in p]
    return tail[-1] if tail else (parts[0] if parts else command)


def _record(kind: Kind, identity: str, exit_code: int, command: str, root: Path, output: str) -> Evidence:
    observed = source_files(root)
    return Evidence(
        kind=kind,
        identity=identity,
        result=Result.PASS if exit_code == 0 else Result.FAIL,
        observed=observed,
        tree=tree_hash(root, observed),
        command=command,
        detail=_tail(output),
        at=time.time(),
    )


def _tail(output: str, lines: int = 3) -> str:
    kept = [ln for ln in output.strip().splitlines() if ln.strip()][-lines:]
    return " | ".join(ln.strip()[:160] for ln in kept)


def _pytest(command: str, output: str, exit_code: int, root: Path) -> list[Evidence]:
    observed = source_files(root)
    tree = tree_hash(root, observed)
    now = time.time()
    records: list[Evidence] = []

    seen: set[str] = set()
    for match in list(PYTEST_NODE.finditer(output)) + list(PYTEST_SHORT.finditer(output)):
        node, status = match.group("node"), match.group("status")
        if node in seen:
            continue
        seen.add(node)
        records.append(
            Evidence(
                kind=Kind.TEST,
                identity=node,
                result=Result.PASS if status == "PASSED" else Result.FAIL,
                observed=observed,
                tree=tree,
                command=command,
                at=now,
            )
        )

    passed = failed = 0
    tail = PYTEST_TAIL.search(output)
    if tail:
        passed = int(tail.group("passed") or 0)
        failed = int(tail.group("failed") or 0) + int(tail.group("errors") or 0)

    records.append(
        Evidence(
            kind=Kind.SUITE,
            identity=_scope(command),
            result=Result.PASS if exit_code == 0 else Result.FAIL,
            observed=observed,
            tree=tree,
            command=command,
            detail=_tail(output),
            passed=passed,
            failed=failed,
            at=now,
        )
    )
    return records


def _js(command: str, output: str, exit_code: int, root: Path, pattern: re.Pattern) -> list[Evidence]:
    match = pattern.search(output)
    passed, failed = _counts(match.group("body")) if match else (0, 0)
    record = _record(Kind.SUITE, _scope(command), exit_code, command, root, output)
    record.passed, record.failed = passed, failed
    return [record]


def _tsc(command: str, output: str, exit_code: int, root: Path) -> list[Evidence]:
    record = _record(Kind.TYPECHECK, _scope(command), exit_code, command, root, output)
    count = TSC_COUNT.search(output)
    record.failed = int(count.group("n")) if count else len(set(TSC_ERROR.findall(output)))
    return [record]


def _go(command: str, output: str, exit_code: int, root: Path) -> list[Evidence]:
    record = _record(Kind.SUITE, _scope(command), exit_code, command, root, output)
    results = GO_RESULT.findall(output)
    record.passed = sum(1 for status, _ in results if status == "ok")
    record.failed = sum(1 for status, _ in results if status != "ok")
    return [record]


def _cargo(command: str, output: str, exit_code: int, root: Path) -> list[Evidence]:
    record = _record(Kind.SUITE, _scope(command), exit_code, command, root, output)
    for _, passed, failed in CARGO_RESULT.findall(output):
        record.passed += int(passed)
        record.failed += int(failed)
    return [record]
