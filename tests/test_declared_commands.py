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


@pytest.mark.parametrize("response", [
    {"interrupted": True, "stdout": "partial"},
    {"timed_out": True, "stdout": "partial"},
    {"unexpected": "shape"},
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


def test_hook_still_ignores_interrupted_undeclared_commands(tmp_path):
    from core.hook import on_post_tool
    from core.ledger import Ledger
    on_post_tool({"tool_name": "Bash", "tool_input": {"command": "npm run anything"},
                  "tool_response": {"interrupted": True}}, tmp_path)
    assert not Ledger.load(tmp_path).evidence


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
    monkeypatch.setattr(verify.subprocess, "run", interrupted)
    receipts = verify.discharge(Ledger(root=tmp_path))
    assert len(receipts) == 1
    assert receipts[0].result is Result.ERROR
    assert receipts[0].execution == "incomplete"
    assert error in receipts[0].detail
