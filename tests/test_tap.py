"""TAP, read as a format rather than as a tool.

Found by pointing the runtime at a real repository outside this project: three
of its four packages run `node --test` and the parsers produced **zero**
records, so a passing run left no evidence and the default `strict` profile
would refuse a stop on work that was genuinely tested.

Design: `docs/design/tap-and-node-test.md`. Every sample below was captured from
Node 22.17.1 and pasted, not remembered - this session has already been wrong
three times about output it had not looked at.

A parser that never reports failure passes every adversarial probe by refusing
everything, and one that never reports success passes every forward probe the
same way, so both directions appear for each shape.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from core.evidence import Kind, Result
from core.parsers import parse

# The default reporter when stdout is not a TTY - which is exactly what a hook
# captures. Trimmed to the summary a `| tail` would leave.
TAP_FAIL = """1..3
# tests 3
# suites 0
# pass 2
# fail 1
# cancelled 0
# skipped 0
"""
TAP_PASS = """1..2
# tests 2
# suites 0
# pass 2
# fail 0
# cancelled 0
# skipped 0
"""
# `--test-reporter=spec`, or a TTY. Same numbers, different marker.
SPEC_FAIL = """ℹ tests 3
ℹ pass 2
ℹ fail 1
"""
SPEC_PASS = """ℹ tests 2
ℹ pass 2
ℹ fail 0
"""
# Plain TAP: a plan and results, no summary counters. What older harnesses and
# `prove` emit.
PLAIN_FAIL = """TAP version 13
ok 1 - adds two numbers
not ok 2 - this one fails
1..2
"""
PLAIN_PASS = """TAP version 13
ok 1 - adds two numbers
ok 2 - trims a string
1..2
"""


@pytest.fixture
def root():
    return Path(tempfile.mkdtemp(prefix="ep-tap-"))


def only(records):
    assert len(records) == 1, records
    return records[0]


# --- forward ----------------------------------------------------------------

def test_a_green_tap_run_is_recorded_as_passing(root):
    got = only(parse('node --test "src/**/*.test.mjs"', TAP_PASS, 0, root))
    assert got.kind is Kind.SUITE
    assert got.result is Result.PASS
    assert (got.passed, got.failed) == (2, 0)
    assert got.counted, "a suite that counted nothing cannot discharge anything"


def test_the_spec_reporter_is_read_too(root):
    """The default flips with whether stdout is a TTY, so both must work."""
    got = only(parse("node --test --test-reporter=spec", SPEC_PASS, 0, root))
    assert (got.result, got.passed, got.failed) == (Result.PASS, 2, 0)


def test_plain_tap_without_counters_is_counted_from_its_results(root):
    """`prove` and older harnesses print a plan and no summary."""
    got = only(parse("prove -r t/", PLAIN_PASS, 0, root))
    assert (got.result, got.passed, got.failed) == (Result.PASS, 2, 0)


# --- adversarial ------------------------------------------------------------

def test_a_failing_run_whose_exit_code_was_eaten_by_a_pipe_is_caught(root):
    """R10, on this runner, reproduced rather than assumed.

        $ node --test ... | tail -6
        # fail 1
        EXIT=0

    The counted failure has to outrank the exit code, or `tail` launders a red
    suite into a green record.
    """
    got = only(parse('node --test "src/**/*.test.mjs" 2>&1 | tail -6', TAP_FAIL, 0, root))
    assert got.result is Result.FAIL, "a failing run was recorded as passing"
    assert (got.passed, got.failed) == (2, 1)


def test_the_spec_reporter_failing_is_caught_the_same_way(root):
    got = only(parse("node --test --test-reporter=spec 2>&1 | tail -6", SPEC_FAIL, 0, root))
    assert got.result is Result.FAIL
    assert (got.passed, got.failed) == (2, 1)


def test_plain_tap_failing_is_caught(root):
    got = only(parse("prove -r t/", PLAIN_FAIL, 0, root))
    assert got.result is Result.FAIL
    assert (got.passed, got.failed) == (1, 1)


def test_a_command_naming_no_runner_at_all_is_still_read(root):
    """The universality case, and the reason this reads output over commands.

    `npm test`, `yarn test` and `turbo test` all emit the TAP above while naming
    nothing. Dispatching on the command would fix one spelling and miss the ones
    people actually type.
    """
    for command in ("npm test", "yarn test", "turbo test", "pnpm -r test"):
        got = only(parse(f"{command} 2>&1 | tail -6", TAP_FAIL, 0, root))
        assert got.result is Result.FAIL, f"{command}: a failing run read as passing"
        assert got.counted, f"{command}: not counted, so it proves nothing"


def test_prose_that_merely_says_pass_and_fail_is_not_a_test_run(root):
    """A command that is not a test run stays unparsed, however it reads."""
    prose = ("The migration should pass 2 checks before you run it.\n"
             "ok so the next step is the rollout\n"
             "it can fail 1 time before alerting\n")
    assert parse("cat notes.md", prose, 0, root) == []


def test_ok_lines_without_a_tap_marker_are_not_counted_as_results(root):
    """The gate, tested where it actually bites.

    An earlier version of this probe used `cat notes.md`, which never reaches
    the TAP parser at all - so removing the marker gate left it passing and it
    proved nothing. Flipping it is what exposed that.

    The gate only matters when a *test command* emits something unrecognisable
    that happens to contain `ok` at the start of a line. Without it, this
    chatter counts as two passing tests and one failure.
    """
    chatter = ("ok 1 connection established\n"
               "ok 2 handshake complete\n"
               "not ok 3 retrying\n")
    got = only(parse("node --test", chatter, 0, root))
    assert not got.counted, "unrecognised output was counted as test results"
    assert (got.passed, got.failed) == (0, 0)


def test_a_node_test_run_this_cannot_read_claims_nothing(root):
    """Silence is honest; a fabricated count is not.

    `counted` stays false, so `Evidence.ran_tests` does not treat it as a
    measured suite and it cannot discharge an obligation on its own.
    """
    got = only(parse("node --test", "some future reporter nobody has seen\n", 1, root))
    assert got.result is Result.FAIL, "the exit code is all there is, and it said 1"
    assert not got.counted


def test_a_wrapped_command_with_no_tap_behaves_exactly_as_before(root):
    """The regression case. `_wrapped` is the fallback for every ecosystem.

    TAP is dispatched *before* the wrapper fallback, so this proves the earlier
    branch did not swallow commands that were already handled.
    """
    mocha = "\n  12 passing (34ms)\n  2 failing\n"
    got = only(parse("npm test", mocha, 1, root))
    assert got.result is Result.FAIL


# --- when the tool cannot read a runner, it says so -------------------------

def _hook(event, payload):
    import json
    import subprocess
    import sys

    return subprocess.run(
        [sys.executable, "-m", "core.hook", event],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=Path(__file__).resolve().parents[1])


def _spots(root):
    from core import blindspots

    return [b for b in blindspots.read(root) if b["kind"] == "unreadable test output"]


def test_a_runner_it_cannot_read_becomes_a_diagnosable_symptom(tmp_path):
    """No runner can be enumerated for every project on earth.

    So the honest position is not "support everything", it is "say when you
    could not read something". A real repository ran `node --test` in three of
    four packages and this runtime produced nothing for any of them - silently,
    and under `strict` that means refusing a stop on tested work.
    """
    _hook("UserPromptSubmit", {"cwd": str(tmp_path), "prompt": "fix the parser bug"})
    # `deno test` is real, current and unknown to this module - the shape of
    # runner an open source user hits on their first day.
    _hook("PostToolUse", {
        "cwd": str(tmp_path), "tool_name": "Bash",
        "tool_input": {"command": "deno test --allow-read"},
        "tool_response": {"stdout": "ok | 12 passed | 0 failed (34ms)\n", "exit_code": 0}})

    found = _spots(tmp_path)
    assert found, "an unreadable test command left no trace at all"
    assert "deno test" in found[-1]["detail"]


def test_a_runner_it_can_read_is_not_reported_as_a_blind_spot(tmp_path):
    """Adversarially: otherwise every green run files a complaint."""
    _hook("UserPromptSubmit", {"cwd": str(tmp_path), "prompt": "fix the parser bug"})
    _hook("PostToolUse", {
        "cwd": str(tmp_path), "tool_name": "Bash",
        "tool_input": {"command": "npm test"},
        "tool_response": {"stdout": TAP_PASS, "exit_code": 0}})

    assert _spots(tmp_path) == [], "a readable run was filed as a blind spot"


def test_a_command_that_never_claimed_to_run_tests_is_not_reported(tmp_path):
    """Adversarially: `git status` is not a silent test failure."""
    _hook("UserPromptSubmit", {"cwd": str(tmp_path), "prompt": "fix the parser bug"})
    _hook("PostToolUse", {
        "cwd": str(tmp_path), "tool_name": "Bash",
        "tool_input": {"command": "git status"},
        "tool_response": {"stdout": "nothing to commit\n", "exit_code": 0}})

    assert _spots(tmp_path) == []


# --- found by attacking the shipped version ---------------------------------

def test_a_text_file_cannot_fabricate_a_passing_suite(root):
    """The worst bug in this change, caught by attacking it after it shipped.

    `TAP_COUNT` briefly accepted a bare letter `i` as the spec reporter's
    marker, so `cat notes.txt` containing "i pass 5" produced a **counted,
    passing** suite record - evidence strong enough to discharge an obligation,
    invented out of a text file. That is the exact failure this project exists
    to refuse, shipped by the feature meant to make it more universal.
    """
    assert parse("cat notes.txt", "i pass 5\n", 0, root) == []


def test_a_range_in_ordinary_output_is_not_a_test_plan(root):
    """`1..10` is a TAP plan and also a thing programs print."""
    assert parse("echo progress", "1..10\n", 0, root) == []


def test_output_shape_alone_does_not_make_a_command_a_test_run(root):
    """The principle, corrected.

    Reading the format decides HOW to parse a test run. It must not decide
    THAT something is one - dispatching on shape alone turned a README with
    `ok 1 install` into a counted passing suite.
    """
    readme = "ok 1 install\nok 2 configure\n1..2\n"
    assert parse("cat README.md", readme, 0, root) == []
    # ...while a command that does claim tests is read exactly as before
    got = only(parse("npm test", readme, 0, root))
    assert (got.passed, got.failed, got.counted) == (2, 0, True)


def test_an_explicit_tap_header_is_taken_at_its_word(root):
    """A deliberate judgement, written down rather than left implicit.

    A script printing `TAP version 13` is declaring itself a TAP producer, so
    it is read as one even though its command name says nothing. That is the
    one case where output alone is allowed to decide, because the output is an
    explicit self-declaration rather than a coincidence of shape.
    """
    got = only(parse("bash deploy.sh", "TAP version 13\nok 1 - deployed\n1..1\n", 0, root))
    assert (got.result, got.passed, got.counted) == (Result.PASS, 1, True)


# --- a monorepo runner, captured from a real turbo run ----------------------

# Trimmed from an actual `npx turbo test` over two workspace packages: one
# failing, one passing. The prefix is the whole problem - every line carries
# the package it came from.
TURBO = """@probe/a:test: not ok 2 - a fails
@probe/a:test: 1..2
@probe/a:test: # tests 2
@probe/a:test: # pass 1
@probe/a:test: # fail 1
@probe/b:test: ok 1 - b passes
@probe/b:test: 1..1
@probe/b:test: # tests 1
@probe/b:test: # pass 1
@probe/b:test: # fail 0
@probe/a#test:  ERROR  command exited (1)

 Tasks:    0 successful, 2 total
Failed:    @probe/a#test
"""


def test_a_monorepo_runner_is_read_through_its_prefix(root):
    """`turbo test` is the root command of a turborepo, and it prefixes lines.

    Measured on a real run rather than assumed: anchoring the TAP patterns hard
    at the line start meant an entire monorepo produced **no records at all**.
    """
    got = only(parse("turbo test", TURBO, 1, root))
    assert got.counted, "a whole monorepo produced nothing"
    assert (got.passed, got.failed) == (2, 1), (got.passed, got.failed)


def test_counts_are_summed_across_packages_not_overwritten(root):
    """The dangerous one, and R10 arriving by a new road.

    An aggregating runner reports per package. Keeping only the last match -
    which a dict comprehension does - meant a failing package followed by a
    passing one reported `fail 0`, laundering a red monorepo into a green
    record. The failing package is deliberately first here, so the bug would be
    invisible to a test that only checked the total looked plausible.
    """
    got = only(parse("turbo test", TURBO, 0, root))   # exit eaten by a pipe
    assert got.failed == 1, "the first package's failure was overwritten"
    assert got.result is Result.FAIL


def test_an_arbitrary_prefixed_line_is_still_not_a_test_run(root):
    """Adversarially: the prefix must not open the door it was closing.

    Allowing `<pkg>:<task>: ` before a TAP marker must not make every
    colon-prefixed log line into test results.
    """
    log = ("deploy:web: # pass 3 of the checks\n"
           "deploy:web: ok 1 connection\n")
    assert parse("cat deploy.log", log, 0, root) == []


def test_a_single_colon_prefix_is_read_too(root):
    """Runners differ, and fixing the prefix at turbo's shape was over-fitting.

    turbo writes `@scope/pkg:task:`; lerna and several pnpm setups write just
    `pkg:`. Requiring two segments read the one tool that had been looked at and
    missed the others - the same mistake as reading a runner by its command
    name, one level down.
    """
    lerna = ("core: 1..2\n"
             "core: # pass 1\n"
             "core: # fail 1\n"
             "web: 1..1\n"
             "web: # pass 1\n"
             "web: # fail 0\n")
    got = only(parse("lerna run test", lerna, 0, root))
    assert got.counted, "a single-colon prefix was not read"
    assert (got.passed, got.failed) == (2, 1)
    assert got.result is Result.FAIL
