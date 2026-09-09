"""Turn test-runner and compiler output into evidence records.

Parsing rather than asking. The agent runs these commands anyway; the runtime
reads the output it already produces. Nothing here prompts a model.

Coverage matters more than precision here. A stack this cannot read produces no
evidence at all, so its obligations can never be discharged and every task on it
is blocked forever. That was a large share of a measured 75 percent false-block
rate, so wrappers and less common runners are handled even when only the exit
code can be recovered.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from .evidence import Evidence, Kind, Result, source_files, tree_hash, vcs_state

PYTEST_TAIL = re.compile(
    r"^=+ (?:(?P<failed>\d+) failed)?,? ?(?:(?P<passed>\d+) passed)?"
    r".*?(?:(?P<errors>\d+) errors?)?.*?=+$",
    re.MULTILINE,
)
PYTEST_NODE = re.compile(r"^(?P<status>PASSED|FAILED|ERROR)\s+(?P<node>\S+::\S+)", re.MULTILINE)
PYTEST_SHORT = re.compile(r"^(?P<node>\S+::\S+)\s+(?P<status>PASSED|FAILED|ERROR)", re.MULTILINE)

JEST_TESTS = re.compile(r"^\s*Tests:\s+(?P<body>.+)$", re.MULTILINE)
VITEST_TESTS = re.compile(r"^\s*Tests\s+(?P<body>.+?)$", re.MULTILINE)

TSC_ERROR = re.compile(r"^(?P<file>[^\s(]+)\((?P<line>\d+),\d+\): error TS\d+", re.MULTILINE)
TSC_COUNT = re.compile(r"Found (?P<n>\d+) errors?", re.MULTILINE)

GO_RESULT = re.compile(r"^(?P<status>ok|FAIL|---\s+FAIL)\s+(?P<pkg>\S+)", re.MULTILINE)
CARGO_RESULT = re.compile(
    r"test result:\s+(?P<status>ok|FAILED)\.\s+(?P<passed>\d+) passed;\s+(?P<failed>\d+) failed",
    re.MULTILINE,
)
RSPEC = re.compile(r"(?P<total>\d+) examples?, (?P<failed>\d+) failures?")
MIX = re.compile(r"(?P<total>\d+) tests?, (?P<failed>\d+) failures?")
PHPUNIT = re.compile(r"Tests: (?P<total>\d+), Assertions: \d+(?:, Failures: (?P<failed>\d+))?")
DOTNET = re.compile(r"Failed:\s*(?P<failed>\d+),\s*Passed:\s*(?P<passed>\d+)", re.I)

# The repeat runner's own machine-readable line. Stability is the one obligation
# that cannot be inferred from an ordinary command, because a single clean run
# of anything looks identical to a hundred of them.
REPEAT = re.compile(
    r"EP-REPEAT verdict=(?P<verdict>\S+) runs=(?P<runs>\d+) passed=(?P<passed>\d+) "
    r"failed=(?P<failed>\d+) rate=(?P<rate>[\d.]+) seconds=(?P<seconds>[\d.]+) "
    r"early=(?P<early>\S+) cmd=(?P<cmd>.+)$",
    re.MULTILINE,
)

WRAPPER = re.compile(
    r"""^\s*(?:[A-Z_]+=\S+\s+)*
    (?: (?:npm|pnpm|yarn|bun)\s+(?:\S+\s+)*?(?:run\s+)?test
      | make\s+(?:\S+\s+)*(?:test|check)
      | (?:tox|nox)\b
      | hatch\s+run\s+test | poetry\s+run\s+(?:pytest|test)
      | just\s+\S*test | bazel\s+test | rake\s+(?:test|spec)
      | gradlew?\s+\S*test | mvn\s+\S*test
      | composer\s+(?:run\s+)?test
      | \./(?:scripts?|bin)/\S*test\S*
      | ctest | swift\s+test | flutter\s+test
    )\b""",
    re.IGNORECASE | re.VERBOSE,
)

# Output that is unmistakably a test runner's summary. Command names cannot
# cover every project's own runner script, so the output is the more reliable
# signal: `python run_tests.py` is a test run whatever it is called.
LOOKS_LIKE_TESTS = re.compile(
    r"""(?: ^=+.*\b\d+\s+(?:passed|failed)\b.*=+$
       | ^\s*Tests:\s+\d
       | \b\d+\s+examples?,\s+\d+\s+failures?\b
       | \bTests\s+run:\s*\d+
       | \btest\s+result:\s+(?:ok|FAILED)\b
       | ^(?:ok|FAIL)\s+\S+\s+[\d.]+s$
       )""",
    re.MULTILINE | re.VERBOSE,
)
# Running the thing and showing what happened. For a project with no test suite
# this is the only proof available, so it has to be recognised or such projects
# can never discharge anything.
RUN_PROGRAM = re.compile(
    r"""^\s*(?:[A-Z_]+=\S+\s+)*
    (?: python3?\s+\S+\.py
      | node\s+\S+\.(?:js|mjs|ts)
      | (?:go|cargo)\s+run
      | ruby\s+\S+\.rb | php\s+\S+\.php
      | \./\S+
      | (?:npm|pnpm|yarn|bun)\s+(?:run\s+)?(?:start|dev)
      | docker\s+compose\s+up
      | curl\s
    )""",
    re.IGNORECASE | re.VERBOSE,
)
BUILD_WRAPPER = re.compile(
    r"""^\s*(?: (?:npm|pnpm|yarn|bun)\s+(?:run\s+)?build
      | make(?:\s+(?:all|build))?\s*$
      | cargo\s+build | go\s+build
      | gradlew?\s+build | mvn\s+\S*(?:package|compile)
      | dotnet\s+build | swift\s+build
    )""",
    re.IGNORECASE | re.VERBOSE,
)


def parse(command: str, output: str, exit_code: int, root: Path) -> list[Evidence]:
    """Evidence implied by one command and its output, or an empty list."""
    cmd = command.strip()
    low = cmd.lower()

    repeat = REPEAT.search(output)
    if repeat:
        return [_stability(repeat, cmd, root)]

    if re.search(r"\b(hyperfine|criterion|benchmark|bench)\b", low) and "test" not in low:
        return [_record(Kind.BENCHMARK, _scope(cmd), exit_code, cmd, root, output)]
    if "pytest" in low:
        return _pytest(cmd, output, exit_code, root)
    if "vitest" in low:
        return [_counted(Kind.SUITE, cmd, output, exit_code, root, VITEST_TESTS)]
    if "jest" in low:
        return [_counted(Kind.SUITE, cmd, output, exit_code, root, JEST_TESTS)]
    if "tsc" in low:
        return [_tsc(cmd, output, exit_code, root)]
    if re.search(r"\bgo test\b", low):
        return [_go(cmd, output, exit_code, root)]
    if re.search(r"\bcargo (test|nextest)\b", low):
        return [_cargo(cmd, output, exit_code, root)]
    if "rspec" in low:
        return [_counted(Kind.SUITE, cmd, output, exit_code, root, RSPEC)]
    if re.search(r"\bmix test\b", low):
        return [_counted(Kind.SUITE, cmd, output, exit_code, root, MIX)]
    if "phpunit" in low:
        return [_counted(Kind.SUITE, cmd, output, exit_code, root, PHPUNIT)]
    if re.search(r"\bdotnet test\b", low):
        return [_counted(Kind.SUITE, cmd, output, exit_code, root, DOTNET)]
    if WRAPPER.match(cmd):
        return [_wrapped(cmd, output, exit_code, root)]
    if BUILD_WRAPPER.match(cmd):
        return [_record(Kind.BUILD, _scope(cmd), exit_code, cmd, root, output)]
    if re.search(r"\b(mypy|pyright)\b", low):
        return [_record(Kind.TYPECHECK, _scope(cmd), exit_code, cmd, root, output)]
    if re.search(r"\b(ruff|eslint|flake8|clippy)\b", low):
        return [_record(Kind.LINT, _scope(cmd), exit_code, cmd, root, output)]
    if LOOKS_LIKE_TESTS.search(output):
        return [_wrapped(cmd, output, exit_code, root)]
    if RUN_PROGRAM.match(cmd):
        return [_record(Kind.RUNTIME, _scope(cmd), exit_code, cmd, root, output)]
    return []


def _counts(body: str) -> tuple[int, int]:
    passed = failed = 0
    for n, word in re.findall(r"(\d+)\s+(passed|failed)", body):
        if word == "passed":
            passed = int(n)
        else:
            failed = int(n)
    return passed, failed


def _scope(command: str) -> str:
    """A stable identity for a command-level record: the target it names."""
    parts = [p for p in command.split() if not p.startswith("-")]
    tail = [p for p in parts[1:] if "/" in p or "." in p or "::" in p]
    return tail[-1] if tail else " ".join(parts[:2]) if parts else command


def _record(kind: Kind, identity: str, exit_code: int, command: str, root: Path,
            output: str) -> Evidence:
    observed = source_files(root)
    return Evidence(
        vcs=vcs_state(root),
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


def _counted(kind: Kind, command: str, output: str, exit_code: int, root: Path,
             pattern: re.Pattern) -> Evidence:
    record = _record(kind, _scope(command), exit_code, command, root, output)
    match = pattern.search(output)
    if not match:
        return record
    groups = match.groupdict()
    if "body" in groups:
        record.passed, record.failed = _counts(groups["body"])
        return record
    failed = int(groups.get("failed") or 0)
    total = int(groups.get("total") or 0)
    record.failed = failed
    record.passed = int(groups.get("passed") or 0) or max(total - failed, 0)
    return record


def _wrapped(command: str, output: str, exit_code: int, root: Path) -> Evidence:
    """A test command whose runner is not visible. The exit code is the evidence.

    Counts are recovered opportunistically: most wrappers pass the underlying
    runner's summary through unchanged.
    """
    record = _record(Kind.SUITE, _scope(command), exit_code, command, root, output)
    for pattern in (JEST_TESTS, PYTEST_TAIL, RSPEC, MIX):
        match = pattern.search(output)
        if not match:
            continue
        groups = match.groupdict()
        if "body" in groups:
            record.passed, record.failed = _counts(groups["body"])
        else:
            failed = int(groups.get("failed") or 0) + int(groups.get("errors") or 0)
            total = int(groups.get("total") or 0)
            record.failed = failed
            record.passed = int(groups.get("passed") or 0) or max(total - failed, 0)
        break
    return record


def _pytest(command: str, output: str, exit_code: int, root: Path) -> list[Evidence]:
    observed = source_files(root)
    tree = tree_hash(root, observed)
    now = time.time()
    records: list[Evidence] = []
    vcs = vcs_state(root)

    seen: set[str] = set()
    for match in list(PYTEST_NODE.finditer(output)) + list(PYTEST_SHORT.finditer(output)):
        node, status = match.group("node"), match.group("status")
        if node in seen:
            continue
        seen.add(node)
        records.append(
            Evidence(
                kind=Kind.TEST, identity=node,
                result=Result.PASS if status == "PASSED" else Result.FAIL,
                observed=observed, tree=tree, command=command, at=now, vcs=vcs,
            )
        )

    passed = failed = 0
    tail = PYTEST_TAIL.search(output)
    if tail:
        passed = int(tail.group("passed") or 0)
        failed = int(tail.group("failed") or 0) + int(tail.group("errors") or 0)

    records.append(
        Evidence(
            kind=Kind.SUITE, identity=_scope(command),
            result=Result.PASS if exit_code == 0 else Result.FAIL,
            observed=observed, tree=tree, command=command, detail=_tail(output),
            passed=passed, failed=failed, at=now, vcs=vcs,
        )
    )
    return records


def _tsc(command: str, output: str, exit_code: int, root: Path) -> Evidence:
    record = _record(Kind.TYPECHECK, _scope(command), exit_code, command, root, output)
    count = TSC_COUNT.search(output)
    record.failed = int(count.group("n")) if count else len(set(TSC_ERROR.findall(output)))
    return record


def _go(command: str, output: str, exit_code: int, root: Path) -> Evidence:
    record = _record(Kind.SUITE, _scope(command), exit_code, command, root, output)
    results = GO_RESULT.findall(output)
    record.passed = sum(1 for status, _ in results if status == "ok")
    record.failed = sum(1 for status, _ in results if status != "ok")
    return record


def _cargo(command: str, output: str, exit_code: int, root: Path) -> Evidence:
    record = _record(Kind.SUITE, _scope(command), exit_code, command, root, output)
    for _, passed, failed in CARGO_RESULT.findall(output):
        record.passed += int(passed)
        record.failed += int(failed)
    return record


def _stability(match: re.Match, command: str, root: Path) -> Evidence:
    runs = int(match.group("runs"))
    failed = int(match.group("failed"))
    record = _record(
        Kind.STABILITY, match.group("cmd").strip(),
        0 if failed == 0 else 1, command, root, "",
    )
    record.runs = runs
    record.passed = int(match.group("passed"))
    record.failed = failed
    record.detail = f"{runs} runs, {failed} failed"
    return record
