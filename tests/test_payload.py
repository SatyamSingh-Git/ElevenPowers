"""Tests for reading host payloads, run against real ones.

`tests/fixtures/real_bash_results.json` holds tool results captured from a
session transcript. They are here because the previous version of this code was
tested only against payloads invented to match what the contract was assumed to
be, and passed every one of them while being wrong about the contract.
"""

import json
from pathlib import Path

import pytest

from core.evidence import Result
from core.parsers import parse
from core.payload import read_result, target_file

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "real_bash_results.json").read_text(encoding="utf-8")
)


def payload(fixture: dict) -> dict:
    failed = isinstance(fixture["result"], str)
    return {
        "hook_event_name": "PostToolUseFailure" if failed else "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": fixture["command"]},
        "tool_result": fixture["result"],
    }


@pytest.mark.parametrize("fixture", FIXTURES, ids=range(len(FIXTURES)))
def test_every_real_result_is_readable(fixture):
    assert read_result(payload(fixture)).readable


@pytest.mark.parametrize("fixture", FIXTURES, ids=range(len(FIXTURES)))
def test_real_results_are_scored_the_way_the_host_scored_them(fixture):
    """The host sends a string when a command failed and an object when it did not."""
    result = read_result(payload(fixture))
    assert result.ok is (fixture["shape"] == "dict")


def test_a_failing_command_carries_its_exit_code_in_the_first_line():
    result = read_result({
        "tool_name": "Bash",
        "tool_result": "Error: Exit code 2\n1 failed, 2 passed in 0.3s\n",
    })
    assert result.exit_code == 2
    assert result.output.startswith("1 failed")


def test_a_spawn_error_with_no_exit_code_still_reads_as_failure():
    assert read_result({"tool_result": "Error: ENAMETOOLONG: name too long"}).exit_code == 1


def test_the_event_name_alone_is_enough_to_know_it_failed():
    """Insurance against the failure string changing shape again."""
    result = read_result({"hook_event_name": "PostToolUseFailure",
                          "tool_result": {"stdout": "boom", "stderr": ""}})
    assert result.exit_code == 1


def test_an_object_with_no_exit_code_is_a_success():
    result = read_result({"tool_result": {"stdout": "3 passed", "stderr": "",
                                          "interrupted": False}})
    assert result.ok and result.output == "3 passed"


def test_an_explicit_exit_code_is_believed_over_everything_else():
    assert read_result({"tool_result": {"stdout": "", "exit_code": 3}}).exit_code == 3


def test_an_interrupted_command_produces_nothing():
    result = read_result({"tool_result": {"stdout": "half", "interrupted": True}})
    assert result.skip == "interrupted"


def test_the_older_field_name_still_works():
    assert read_result({"tool_response": {"stdout": "ok"}}).output == "ok"


def test_content_blocks_are_flattened():
    result = read_result({"tool_result": [{"type": "text", "text": "3 passed"}]})
    assert result.output == "3 passed"


def test_a_shape_with_no_result_at_all_is_reported_rather_than_assumed():
    assert read_result({"tool_name": "Bash", "tool_input": {}}).readable is False


def test_target_file_reads_both_file_and_notebook_paths():
    assert target_file({"tool_input": {"file_path": "a.py"}}) == "a.py"
    assert target_file({"tool_input": {"notebook_path": "b.ipynb"}}) == "b.ipynb"


def test_a_failing_test_run_becomes_failing_evidence(tmp_path):
    """The end-to-end shape of the defect this module exists to fix."""
    result = read_result({
        "hook_event_name": "PostToolUseFailure",
        "tool_name": "Bash",
        "tool_input": {"command": "python -m pytest tests -q"},
        "tool_result": "Error: Exit code 1\nF..\n1 failed, 2 passed in 0.31s\n",
    })
    records = parse("python -m pytest tests -q", result.output, result.exit_code, tmp_path)
    assert records and records[-1].result is Result.FAIL
    assert records[-1].failed == 1
