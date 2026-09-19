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
# `pytest -q` ends with a bare summary and no rule of equals signs around it, so
# the decorated pattern above recovers no counts from the quiet mode that most
# agents actually use.
PYTEST_QUIET = re.compile(r"^(?P<body>\d+ [a-z]+(?:, \d+ [a-z]+)*)\s+in\s+[\d.]+s", re.MULTILINE)

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
       | ^\d+\s+(?:passed|failed)(?:,\s*\d+\s+[a-z]+)*\s+in\s+[\d.]+s
       | ^\s*Tests:\s+\d
       | \b\d+\s+examples?,\s+\d+\s+failures?\b
       | \bTests\s+run:\s*\d+
       | \btest\s+result:\s+(?:ok|FAILED)\b
       | ^(?:ok|FAIL)\s+\S+\s+[\d.]+s$
       )""",
    re.MULTILINE | re.VERBOSE,
)
# TAP, which is a format rather than a tool. `node --test`, `tap`, `ava --tap`,
# `prove` and assorted C, Go and Rust harnesses all emit it, so reading the
# format covers runners this file has never heard of.
#
# Two reporters, both captured from Node 22.17.1 rather than remembered:
#   TAP   `# pass 2` / `# fail 1`      - the default when stdout is not a TTY,
#                                        which is exactly what a hook sees
#   spec  `ℹ pass 2` / `ℹ fail 1`    - `--test-reporter=spec`, or a TTY
# `#` and the spec reporter's information sign, and NOT a bare letter `i`: that
# was here for a moment and `cat notes.txt` containing "i pass 5" came back as a
# counted, passing suite. Fabricated evidence from a text file is the exact
# failure this whole project exists to refuse.
# A monorepo runner prefixes every line with the package it came from:
# `@probe/a:test: # pass 1` is what turbo emits, and a turborepo's root command
# is `turbo test`. Anchoring hard at the line start meant an entire monorepo
# produced no records at all - measured on a real turbo run, not assumed.
# One or two colon-separated segments, because runners differ: turbo writes
# `@scope/pkg:task:`, lerna and several pnpm setups write just `pkg:`. Fixing
# the count at two was fitting the pattern to the one tool that had been looked
# at, which is the same mistake as reading a runner by its command name.
TAP_PREFIX = r"(?:(?:[^\s:]+:){1,2}[ \t]*)?"
TAP_COUNT = re.compile(r"^" + TAP_PREFIX + r"\s*(?:#|ℹ)\s*(?P<word>pass|fail)\s+(?P<n>\d+)\s*$",
                       re.MULTILINE)
# The strong, self-declaring header. A bare `1..10` plan line is not enough on
# its own to call something a test run - `echo progress` printing a range said
# so too.
TAP_VERSION = re.compile(r"^" + TAP_PREFIX + r"TAP version \d+\s*$", re.MULTILINE)
# The output declaring itself TAP. Counting `ok` lines without this gate turns
# any log with a line starting `ok` into test results, which is the
# false-positive class this project has already paid for four times.
TAP_MARKER = re.compile(r"^" + TAP_PREFIX + r"(?:TAP version \d+|1\.\.\d+)\s*$",
                        re.MULTILINE)
TAP_RESULT = re.compile(r"^" + TAP_PREFIX + r"(?P<bad>not )?ok\s+\d+\b", re.MULTILINE)

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
# Real commands rarely begin with the thing they run. Across 36,000 commands
# replayed from real sessions, `cd <dir> && ...` and `export VAR=... && ...`
# were the two commonest openings, and every anchored pattern here missed all of
# them: `cd api && npm run build` was not a build, and its identity came out as
# the directory rather than the command.
PREFIX = re.compile(
    r"""^\s*(?: cd\s+(?:"[^"]*"|'[^']*'|\S+)
              | export\s+[A-Za-z_]\w*=(?:"[^"]*"|'[^']*'|\S*)
              | set\s+-[a-z]+
              | source\s+\S+
        )\s*(?:&&|;)\s*""",
    re.VERBOSE,
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


# Agents write files through the shell as often as through an edit tool. In a
# corpus of 36,000 real commands, `cat > file` alone appeared 1,431 times, and
# 637 turns changed the repository without touching an edit tool at all. A
# runtime watching only the edit tools is blind to all of them.
WRITE_TARGET = re.compile(
    r""" >>?\s*(?P<redirect>[\w./\\-]+)
       | \btee\s+(?:-a\s+)?(?P<tee>[\w./\\-]+)
       | \bsed\s+-i(?:\.\w+)?\s+(?:-e\s+)?(?:'[^']*'\s+|"[^"]*"\s+)?(?P<sed>[\w./\\-]+)
    """,
    re.VERBOSE,
)


def written_paths(command: str) -> list[str]:
    """Files this command wrote to, as best as a shell line can be read.

    Deliberately narrow: a target needs a file extension, which rules out `>&2`,
    process substitution and most of the ways a redirect is not a file. The
    consequence of a wrong guess here is a path added to the task's touched set,
    so under-reading is much cheaper than over-reading.
    """
    out = []
    for match in WRITE_TARGET.finditer(command):
        target = next(g for g in match.groups() if g)
        if target.startswith("/dev/") or "." not in Path(target).name:
            continue
        out.append(target)
    return out


def _bare(command: str) -> str:
    """A command with its setup prefixes removed, so the runner is at the front."""
    text = command.strip()
    while True:
        shorter = PREFIX.sub("", text, count=1)
        if shorter == text:
            return text
        text = shorter


# Harnesses whose whole job is to run tests and emit TAP, matched at the front
# of the command so they are a *runner name* and not a word appearing anywhere.
# `\btap\b` unanchored would match `cat fixture.tap`, which is the exact hole
# this is here to close.
TAP_RUNNER = re.compile(r"^(?:prove|bats|tap|tape)$", re.IGNORECASE)


def runs_tap(command: str) -> bool:
    """Does this command name a TAP harness?

    An allow-list of runners, which is the opposite of a deny-list of shell
    words: an unknown command produces no record rather than a wrong one, and
    the failure mode of a missing entry is silence plus a blindspot.
    """
    bare = _bare(command)
    if re.search(r"\bnode\s+--test\b", bare.lower()):
        return True
    first = bare.split()
    return bool(first) and bool(TAP_RUNNER.match(first[0].rsplit("/", 1)[-1]))


def looks_like_tap(output: str) -> bool:
    """Is this text a TAP report, whatever produced it?

    Shape only. Whether anything *ran* is a question about the command, and
    keeping the two apart is the point - `cat fixture.tap` satisfies this and
    ran no test at all. Used to turn that case into a blindspot rather than
    either a false record or a silent drop.
    """
    return bool(TAP_VERSION.search(output) or TAP_MARKER.search(output)
                or TAP_COUNT.search(output))


def claims_to_run_tests(command: str) -> bool:
    """Does this command say it runs tests, whatever runner it uses?

    Deliberately broad, because it decides whether *silence is worth reporting*
    rather than what a record says. No runner can be enumerated for every
    project on earth, so the honest position is that an unreadable test command
    becomes a diagnosable symptom instead of a tool that quietly went quiet -
    which is the same rule `blindspots.py` already applies to host payloads.

    Found the hard way: a real repository ran `node --test` in three of its four
    packages, this module produced nothing for any of them, and nobody could
    have known without reading the parsers.
    """
    return bool(WRAPPER.match(_bare(command))
                or re.search(r"\b(tests?|specs?)\b", command.lower()))


def parse(command: str, output: str, exit_code: int, root: Path) -> list[Evidence]:
    """Evidence implied by one command and its output, or an empty list."""
    cmd = command.strip()
    bare = _bare(cmd)
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
    # Before the wrapper fallback, and deliberately: a command name is not a
    # runner. `npm test`, `yarn test` and `turbo test` all emit the TAP below
    # while naming nothing, and `_wrapped` would only trust their exit code.
    # Dispatching on the OUTPUT is what makes this work for a runner this file
    # has never heard of, which is the point of reading a format rather than a
    # tool.
    # The output decides HOW to read a test run. It must not decide THAT
    # something is one: dispatching on shape alone made `cat README.md` with
    # `ok 1 install` into a counted passing suite.
    #
    # The `TAP version 13` header was the one exception, on the reasoning that a
    # header is a self-declaration rather than a coincidence of shape. An audit
    # pointed `cat fixture.tap` at it and got a counted passing suite with
    # ran_tests true out of a file read. The declaration is in the *file*; the
    # question is about the *run*; output cannot tell those apart. So the
    # exception is gone, and both halves are required: a command that runs tests
    # - it names a TAP harness, or says `test` like `npm test` and `turbo test`
    # do - and output that is TAP.
    #
    # The cost, stated rather than discovered: `bash ci.sh` emitting TAP now
    # produces no record. It produces a *blindspot* instead (`core/hook.py`), so
    # it is a diagnosable silence rather than a quiet one.
    # A named harness is read whatever it printed - unreadable output from a
    # known runner becomes an honest uncounted record, which is the existing
    # design and not something this change touches. Shape is required only where
    # the command is merely *claiming* tests.
    if runs_tap(cmd) or (claims_to_run_tests(cmd) and looks_like_tap(output)):
        return [_tap(cmd, output, exit_code, root)]
    if WRAPPER.match(bare):
        return [_wrapped(cmd, output, exit_code, root)]
    if BUILD_WRAPPER.match(bare):
        return [_record(Kind.BUILD, _scope(cmd), exit_code, cmd, root, output)]
    # `npm run typecheck` and `npx turbo typecheck` were among the commonest
    # unrecognised commands in the replayed corpus. The script name is the same
    # across ecosystems, and this is an obligation agents otherwise cannot
    # discharge on a TypeScript project that does not call `tsc` directly.
    if re.search(r"\b(mypy|pyright|typecheck|type-check)\b", low):
        return [_record(Kind.TYPECHECK, _scope(cmd), exit_code, cmd, root, output)]
    if re.search(r"\b(ruff|eslint|flake8|clippy)\b", low):
        return [_record(Kind.LINT, _scope(cmd), exit_code, cmd, root, output)]
    if LOOKS_LIKE_TESTS.search(output):
        return [_wrapped(cmd, output, exit_code, root)]
    if RUN_PROGRAM.match(bare):
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
    parts = [p for p in _bare(command).split() if not p.startswith("-")]
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
        scope="source",
        command=command,
        detail=_tail(output),
        at=time.time(),
    )


def _counts_decide(record: Evidence) -> Evidence:
    """A counted failure outranks the exit code.

    Every parser below calls `_record`, which has nothing but the exit code to
    go on, and *then* fills in the counts. Unless the verdict is revisited
    afterwards the counts are decoration — which is what they were:
    `pytest ... | tail -80` exits with `tail`'s status, and **123 of the 295
    preserved passing suite records in `results/` say PASS while holding a
    non-zero failure count**, the worst at `failed=87, passed=1339`.

    The exit code still decides when nothing was counted. A runner this module
    does not recognise is exactly the case that rule exists for, and a record
    that counted nothing is already disqualified by `Evidence.ran_tests`.
    """
    if record.failed:
        record.result = Result.FAIL
    return record


def _tail(output: str, lines: int = 3) -> str:
    kept = [ln for ln in output.strip().splitlines() if ln.strip()][-lines:]
    return " | ".join(ln.strip()[:160] for ln in kept)


def _counted(kind: Kind, command: str, output: str, exit_code: int, root: Path,
             pattern: re.Pattern) -> Evidence:
    record = _record(kind, _scope(command), exit_code, command, root, output)
    record.counted = kind is Kind.SUITE
    match = pattern.search(output)
    if not match:
        return record
    groups = match.groupdict()
    if "body" in groups:
        record.passed, record.failed = _counts(groups["body"])
        return _counts_decide(record)
    failed = int(groups.get("failed") or 0)
    total = int(groups.get("total") or 0)
    record.failed = failed
    record.passed = int(groups.get("passed") or 0) or max(total - failed, 0)
    return _counts_decide(record)


def _tap(command: str, output: str, exit_code: int, root: Path) -> Evidence:
    """A TAP 13 run, by whichever tool produced it.

    Counters first, because they are exact and both of Node's reporters emit
    them. Falling back to counting result lines for producers that print a plan
    and no summary, which plain TAP from older harnesses does.

    The exit code is not trusted over the counts. `node --test ... | tail -6`
    exits **0** while `# fail 1` sits in the output - R10, reproduced on this
    runner rather than assumed - so the verdict goes through `_counts_decide`
    like every other counting parser here.
    """
    record = _record(Kind.SUITE, _scope(command), exit_code, command, root, output)

    # SUMMED, not taken one at a time. An aggregating runner reports per
    # package, and a dict comprehension kept only the last one: `turbo test`
    # over a failing package followed by a passing one reported `fail 0`,
    # laundering a red monorepo into a green record. R10 arriving by a new road.
    counts = {"pass": 0, "fail": 0}
    counted_any = False
    for match in TAP_COUNT.finditer(output):
        counts[match.group("word")] += int(match.group("n"))
        counted_any = True
    if counted_any:
        record.passed = counts["pass"]
        record.failed = counts["fail"]
        record.counted = True
        return _counts_decide(record)

    if TAP_MARKER.search(output):
        results = TAP_RESULT.findall(output)
        if results:
            record.failed = sum(1 for bad in results if bad)
            record.passed = len(results) - record.failed
            record.counted = True
            return _counts_decide(record)

    # It named `node --test` but said nothing this can read. The exit code is
    # all there is, and `counted` stays false so `Evidence.ran_tests` does not
    # treat it as a measured suite.
    return record


def _wrapped(command: str, output: str, exit_code: int, root: Path) -> Evidence:
    """A test command whose runner is not visible. The exit code is the evidence.

    Counts are recovered opportunistically: most wrappers pass the underlying
    runner's summary through unchanged.
    """
    record = _record(Kind.SUITE, _scope(command), exit_code, command, root, output)
    for pattern in (JEST_TESTS, PYTEST_TAIL, PYTEST_QUIET, RSPEC, MIX):
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
    return _counts_decide(record)


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
                observed=observed, tree=tree, scope="source", command=command,
                at=now, vcs=vcs,
            )
        )

    passed = failed = 0
    tail = PYTEST_TAIL.search(output)
    if tail:
        passed = int(tail.group("passed") or 0)
        failed = int(tail.group("failed") or 0) + int(tail.group("errors") or 0)
    else:
        quiet = PYTEST_QUIET.search(output)
        if quiet:
            passed, failed = _counts(quiet.group("body"))

    records.append(
        Evidence(
            kind=Kind.SUITE, identity=_scope(command),
            result=Result.PASS if exit_code == 0 else Result.FAIL,
            observed=observed, tree=tree, scope="source", command=command,
            detail=_tail(output), passed=passed, failed=failed, counted=True,
            at=now, vcs=vcs,
        )
    )
    _counts_decide(records[-1])
    return records


def _tsc(command: str, output: str, exit_code: int, root: Path) -> Evidence:
    record = _record(Kind.TYPECHECK, _scope(command), exit_code, command, root, output)
    count = TSC_COUNT.search(output)
    record.failed = int(count.group("n")) if count else len(set(TSC_ERROR.findall(output)))
    return _counts_decide(record)


def _go(command: str, output: str, exit_code: int, root: Path) -> Evidence:
    record = _record(Kind.SUITE, _scope(command), exit_code, command, root, output)
    results = GO_RESULT.findall(output)
    record.passed = sum(1 for status, _ in results if status == "ok")
    record.failed = sum(1 for status, _ in results if status != "ok")
    return _counts_decide(record)


def _cargo(command: str, output: str, exit_code: int, root: Path) -> Evidence:
    record = _record(Kind.SUITE, _scope(command), exit_code, command, root, output)
    for _, passed, failed in CARGO_RESULT.findall(output):
        record.passed += int(passed)
        record.failed += int(failed)
    return _counts_decide(record)


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
