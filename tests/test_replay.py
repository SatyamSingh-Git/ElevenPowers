"""Tests for reading a session transcript back into events.

The fixture is a hand-built transcript rather than a captured one, because a
real session is megabytes and mostly irrelevant. What was captured from a real
session is the shape of each row, which is what these assert.
"""

import json
from pathlib import Path

import pytest

from eval.replay import head, read_result_v0
from eval.transcript import load

ROWS = [
    {"type": "user", "cwd": "/repo", "isSidechain": False,
     "message": {"role": "user", "content": [{"type": "text", "text": "fix the login bug"}]}},
    {"type": "assistant", "cwd": "/repo", "isSidechain": False,
     "message": {"role": "assistant", "content": [
         {"type": "tool_use", "id": "t1", "name": "Read",
          "input": {"file_path": "/repo/src/login.py"}}]}},
    {"type": "user", "cwd": "/repo", "isSidechain": False,
     "message": {"role": "user", "content": [
         {"type": "tool_result", "tool_use_id": "t1", "content": "..."}]},
     "toolUseResult": {"type": "text", "file": {"filePath": "/repo/src/login.py"}}},
    {"type": "assistant", "cwd": "/repo", "isSidechain": False,
     "message": {"role": "assistant", "content": [
         {"type": "tool_use", "id": "t2", "name": "Bash",
          "input": {"command": "python -m pytest tests -q"}}]}},
    {"type": "user", "cwd": "/repo", "isSidechain": False,
     "message": {"role": "user", "content": [
         {"type": "tool_result", "tool_use_id": "t2", "content": "..."}]},
     "toolUseResult": "Error: Exit code 1\n1 failed, 2 passed in 0.4s\n"},
    {"type": "assistant", "cwd": "/repo", "isSidechain": False,
     "message": {"role": "assistant", "content": [{"type": "text", "text": "One test fails."}]}},
    # A subagent's rows are a different agent's work and are skipped by default.
    {"type": "assistant", "cwd": "/repo", "isSidechain": True,
     "message": {"role": "assistant", "content": [
         {"type": "tool_use", "id": "t3", "name": "Bash", "input": {"command": "ls"}}]}},
    # Host-injected user text is not a person asking for anything.
    {"type": "user", "cwd": "/repo", "isSidechain": False,
     "message": {"role": "user", "content": "<task-notification>done</task-notification>"}},
]


@pytest.fixture
def transcript(tmp_path):
    path = tmp_path / "session.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in ROWS), encoding="utf-8")
    return path


def test_a_turn_is_a_prompt_with_the_calls_that_followed_it(transcript):
    turns = load(transcript)
    assert len(turns) == 1
    assert turns[0].prompt == "fix the login bug"
    assert [c.name for c in turns[0].calls] == ["Read", "Bash"]
    assert turns[0].last_message == "One test fails."


def test_a_string_result_is_read_as_the_failure_it_is(transcript):
    bash = load(transcript)[0].calls[1]
    assert bash.failed
    assert bash.payload("/repo")["hook_event_name"] == "PostToolUseFailure"


def test_an_object_result_is_read_as_success(transcript):
    read = load(transcript)[0].calls[0]
    assert not read.failed


def test_subagent_rows_are_left_out_unless_asked_for(transcript):
    assert all(c.args.get("command") != "ls" for c in load(transcript)[0].calls)
    assert any(c.args.get("command") == "ls"
               for t in load(transcript, include_subagents=True) for c in t.calls)


def test_the_previous_reader_scored_that_failure_as_a_success(transcript):
    """The defect, stated as a test so it cannot come back quietly."""
    bash = load(transcript)[0].calls[1]
    _, exit_code = read_result_v0(bash.payload("/repo"))
    assert exit_code == 0


def test_commands_are_grouped_by_what_they_run_not_where(tmp_path):
    assert head('cd "/repo" && npm run build') == "npm run"
    assert head("python -m pytest tests -q") == "python pytest"
