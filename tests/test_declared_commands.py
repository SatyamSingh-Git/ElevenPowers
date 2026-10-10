"""Project declarations authorize recognition, not guessed command names."""
import pytest

from core.config import Config, save
from core.evidence import Kind, Result
from core.parsers import parse


@pytest.mark.parametrize("command", ["npm run ci", "bash quality.sh", "python tools/check_all.py"])
def test_exact_project_command_is_a_suite(tmp_path, command):
    save(tmp_path, Config(commands={"tests": command}))
    rows = parse(command, "all checks complete", 0, tmp_path)
    assert len(rows) == 1
    assert rows[0].kind is Kind.SUITE
    assert rows[0].result is Result.PASS
    assert rows[0].execution == "complete"
    assert not rows[0].counted  # A command receipt is not an invented test count.


def test_declaration_is_not_a_prefix_or_output_authorization(tmp_path):
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    assert parse("npm run ci-extra", "", 0, tmp_path) == []
    assert parse("cat results.tap", "TAP version 13\n1..1\nok 1 good", 0, tmp_path) == []


@pytest.mark.parametrize("code,expected", [(0, Result.PASS), (1, Result.FAIL), (None, Result.ERROR)])
def test_declared_outcomes_include_incomplete(tmp_path, code, expected):
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    record = parse("npm run ci", "", code, tmp_path)[0]
    assert record.result is expected
    assert record.execution == ("incomplete" if code is None else "complete")


def test_counted_failure_overrides_zero_exit_and_later_passing_package(tmp_path):
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    output = "a: # pass 2\na: # fail 1\nb: # pass 3\nb: # fail 0\n"
    record = parse("npm run ci", output, 0, tmp_path)[0]
    assert record.result is Result.FAIL
    assert (record.passed, record.failed) == (5, 1)


def test_incomplete_replaces_previous_success(tmp_path):
    from core.obligations import SUITE_GREEN
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    passed = parse("npm run ci", "", 0, tmp_path)[0]
    incomplete = parse("npm run ci", "partial output", None, tmp_path)[0]
    assert passed.identity == incomplete.identity
    assert SUITE_GREEN.satisfied_by([passed, incomplete]) is None


# Captured from Claude Code 2.1.292 on 2026-10-11: a Bash call past its tool
# timeout is moved to the background and arrives as an ordinary PostToolUse with
# no exit code. The installed advice exercise recorded exactly this as a pass.
TIMED_OUT = {"stdout": "", "stderr": "", "interrupted": False, "isImage": False,
             "noOutputExpected": False, "backgroundTaskId": "bu74sk7wh", "timedOutAfterMs": 3000}
COMPLETED = {"stdout": "second", "stderr": "", "interrupted": False, "isImage": False,
             "noOutputExpected": False}


@pytest.mark.parametrize("response", [
    {"interrupted": True, "stdout": "partial"},
    {"timed_out": True, "stdout": "partial"},
    {"unexpected": "shape"},
    TIMED_OUT,
    {k: v for k, v in TIMED_OUT.items() if k != "timedOutAfterMs"},
    {k: v for k, v in TIMED_OUT.items() if k != "backgroundTaskId"},
])
def test_hook_records_incomplete_declared_execution(tmp_path, response):
    from core.hook import on_post_tool
    from core.ledger import Ledger
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    on_post_tool({"tool_name": "Bash", "tool_input": {"command": "npm run ci"},
                  "tool_response": response}, tmp_path)
    records = Ledger.load(tmp_path).evidence
    assert len(records) == 1
    assert records[0].execution == "incomplete"
    assert records[0].result is Result.ERROR


@pytest.mark.parametrize("response", [{"interrupted": True}, TIMED_OUT])
def test_hook_still_ignores_interrupted_undeclared_commands(tmp_path, response):
    from core.hook import on_post_tool
    from core.ledger import Ledger
    on_post_tool({"tool_name": "Bash", "tool_input": {"command": "python -m pytest -q"},
                  "tool_response": response}, tmp_path)
    assert not Ledger.load(tmp_path).evidence


def test_the_same_host_shape_completed_is_still_a_pass(tmp_path):
    from core.hook import on_post_tool
    from core.ledger import Ledger
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    on_post_tool({"tool_name": "Bash", "tool_input": {"command": "npm run ci"},
                  "tool_response": COMPLETED}, tmp_path)
    (record,) = Ledger.load(tmp_path).evidence
    assert (record.result, record.execution) == (Result.PASS, "complete")


@pytest.mark.parametrize("error", ["timeout", "launch"])
def test_automatic_verification_retains_incomplete_attempt(tmp_path, monkeypatch, error):
    import subprocess
    from core import verify
    from core.ledger import Ledger
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    monkeypatch.setattr(verify, "dischargeable", lambda ledger: ["tests"])
    def interrupted(*args, **kwargs):
        if error == "timeout":
            raise subprocess.TimeoutExpired("npm run ci", 1, output=b"partial")
        raise OSError("cannot launch")
    monkeypatch.setattr(verify, "run_command", interrupted)
    receipts = verify.discharge(Ledger(root=tmp_path))
    assert len(receipts) == 1
    assert receipts[0].result is Result.ERROR
    assert receipts[0].execution == "incomplete"
    assert error in receipts[0].detail


def test_mixed_monorepo_summaries_keep_failure_from_any_runner(tmp_path):
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    output = ("web:test: \x1b[31m Tests  1 failed | 8 passed (9)\x1b[0m\n"
              "worker:test: # pass 12\nworker:test: # fail 0\n")
    receipt = parse("npm run ci", output, 0, tmp_path)[0]
    assert receipt.result is Result.FAIL
    assert (receipt.passed, receipt.failed) == (20, 1)


def test_declared_zero_test_summary_is_not_suite_proof(tmp_path):
    save(tmp_path, Config(commands={"tests": "bash quality.sh"}))
    receipt = parse("bash quality.sh", "Tests  0 passed (0)", 0, tmp_path)[0]
    assert receipt.counted
    assert not receipt.ran_tests


def test_same_declared_command_can_supply_distinct_needs(tmp_path):
    save(tmp_path, Config(commands={"tests": "check-all", "typecheck": "check-all"}))
    receipts = parse("check-all", "checks complete", 0, tmp_path)
    assert {r.kind for r in receipts} == {Kind.SUITE, Kind.TYPECHECK}
    assert len({(r.kind, r.identity) for r in receipts}) == 2


@pytest.mark.parametrize("summary", [
    "test result: FAILED. 0 passed; 1 failed; 0 ignored",
    "=== 1 passed, 1 error in 0.01s ===",
    "3 examples, 1 failure",
    "3 tests, 1 failure",
    "Tests: 3, Assertions: 3, Failures: 1",
    "Failed: 1, Passed: 2",
    "FAIL example/package 0.01s",
    "worker:test: FAIL example/package 0.01s",
    "worker:test: === 1 passed, 1 error in 0.01s ===",
    "worker:test: 1 passed, 1 error in 0.01s",
])
def test_mixed_runner_failure_is_not_hidden_by_tap(tmp_path, summary):
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    receipt = parse("npm run ci", summary + "\n# pass 2\n# fail 0\n", 0, tmp_path)[0]
    assert receipt.result is Result.FAIL
    assert receipt.failed >= 1


def test_declared_target_preserves_scope_and_historical_identity(tmp_path):
    from core.obligations import SUITE_GREEN, TEST_ADDED
    command = "pytest tests/test_api.py -q"
    save(tmp_path, Config(commands={"tests": command}))
    receipt = parse(command, "1 passed in 0.01s", 0, tmp_path)[0]
    assert not SUITE_GREEN.matches(receipt)
    assert TEST_ADDED.matches(receipt)
    save(tmp_path, Config())
    old = parse("npm test", "", 1, tmp_path)[0]
    save(tmp_path, Config(commands={"tests": "npm test"}))
    new = parse("npm test", "", 0, tmp_path)[0]
    assert SUITE_GREEN.satisfied_by([old, new]) is new


def test_incomplete_is_not_reproduced_failure(tmp_path):
    from core.obligations import _demonstrated_fix
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    before = parse("npm run ci", "", None, tmp_path)[0]
    after = parse("npm run ci", "", 0, tmp_path)[0]
    assert _demonstrated_fix([before, after]) is None


def test_incomplete_is_not_preexisting_breakage(tmp_path):
    from core.ledger import Ledger
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    ledger = Ledger(root=tmp_path)
    ledger.evidence = parse("npm run ci", "", None, tmp_path)
    assert ledger.pre_existing() == []


def test_completed_failure_after_interruption_can_prove_fix(tmp_path):
    from core.obligations import _demonstrated_fix
    save(tmp_path, Config(commands={"tests": "npm run ci"}))
    records = [parse("npm run ci", "", code, tmp_path)[0] for code in (None, 1, 0)]
    assert _demonstrated_fix(records) is records[-1]
    records += parse("npm run ci", "", None, tmp_path)
    assert _demonstrated_fix(records) is None
