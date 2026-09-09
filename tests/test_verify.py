"""Computing the missing evidence rather than demanding it.

In every one of fifteen blocked live runs the agent had written a test and run
it; what it had not done was run the whole suite, which is a second invocation
of the same tool. Blocking to make it happen costs another agent turn. Running
it costs seconds and no tokens.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.config import Config, save
from core.evidence import Result
from core.ledger import Ledger, Status
from core.obligations import Claim
from core.verify import discharge, dischargeable

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text(
        "import sys; sys.path.insert(0, '.')\n"
        "from src.app import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    return tmp_path


def open_task(root):
    """A task that has changed the code and its test, which is the usual shape."""
    return Ledger(root=root, request="fix the addition bug", claims=[Claim.BUG_FIXED],
                  seen=["src/app.py", "tests/test_app.py"])


def test_nothing_runs_without_a_declared_command(project):
    assert dischargeable(open_task(project)) == []
    assert discharge(open_task(project)) == []


def test_a_declared_command_covers_the_unmet_need(project):
    save(project, Config(commands={"tests": f'"{sys.executable}" -m pytest -q'}))
    assert "tests" in dischargeable(open_task(project))


def test_running_it_produces_evidence_that_settles_the_claim(project):
    save(project, Config(commands={"tests": f'"{sys.executable}" -m pytest -q'}))
    ledger = open_task(project)
    assert ledger.status() is not Status.VERIFIED
    ledger.add(discharge(ledger))
    assert ledger.status() is Status.VERIFIED


def test_a_failing_suite_is_recorded_faithfully(project):
    """The point is to find out, not to manufacture a green result."""
    (project / "tests" / "test_app.py").write_text(
        "def test_broken():\n    assert False\n", encoding="utf-8")
    save(project, Config(commands={"tests": f'"{sys.executable}" -m pytest -q'}))
    ledger = open_task(project)
    ledger.add(discharge(ledger))
    assert ledger.status() is not Status.VERIFIED
    assert any(e.result is not Result.PASS for e in ledger.evidence)


def test_emptying_a_test_file_does_not_count_as_writing_one(project):
    """How a suite goes green without the bug being fixed."""
    save(project, Config(commands={"tests": f'"{sys.executable}" -m pytest -q'}))
    (project / "tests" / "test_app.py").write_text("", encoding="utf-8")
    ledger = open_task(project)
    ledger.add(discharge(ledger))
    assert ledger.status() is not Status.VERIFIED


def test_a_command_that_cannot_run_is_survivable(project):
    save(project, Config(commands={"tests": "definitely-not-a-command --please"}))
    ledger = open_task(project)
    discharge(ledger)
    assert ledger.status() is not Status.VERIFIED


def test_what_was_run_is_recorded(project):
    save(project, Config(commands={"tests": f'"{sys.executable}" -m pytest -q'}))
    ledger = open_task(project)
    discharge(ledger)
    assert any(d["what"] == "ran a declared command" for d in ledger.decisions)


# --- through the hook -------------------------------------------------------

def run_hook(event, payload):
    return subprocess.run(
        [sys.executable, "-m", "core.hook", event],
        input=json.dumps(payload), capture_output=True, text=True, cwd=REPO_ROOT,
    )


def test_the_gate_does_not_block_what_it_can_check_itself(project):
    """The shape of three quarters of blocked live runs: a fix, a test, no suite run."""
    save(project, Config(commands={"tests": f'"{sys.executable}" -m pytest -q'}))
    run_hook("UserPromptSubmit", {"cwd": str(project), "prompt": "fix the addition bug"})
    for rel in ("src/app.py", "tests/test_app.py"):
        run_hook("PostToolUse", {
            "cwd": str(project), "tool_name": "Edit",
            "tool_input": {"file_path": str(project / rel)},
            "tool_result": {"filePath": "x"},
        })
    stop = run_hook("Stop", {"cwd": str(project), "last_assistant_message": "fixed it"})
    assert stop.returncode == 0, stop.stderr


def test_it_still_blocks_when_no_test_was_written(project):
    """Running the suite is not evidence that this change is covered."""
    save(project, Config(commands={"tests": f'"{sys.executable}" -m pytest -q'}))
    run_hook("UserPromptSubmit", {"cwd": str(project), "prompt": "fix the addition bug"})
    run_hook("PostToolUse", {
        "cwd": str(project), "tool_name": "Edit",
        "tool_input": {"file_path": str(project / "src" / "app.py")},
        "tool_result": {"filePath": "x"},
    })
    stop = run_hook("Stop", {"cwd": str(project), "last_assistant_message": "fixed it"})
    assert stop.returncode == 2
    assert "a test covering the change" in stop.stderr


def test_it_still_blocks_when_the_suite_it_ran_is_red(project):
    (project / "tests" / "test_app.py").write_text(
        "def test_broken():\n    assert False\n", encoding="utf-8")
    save(project, Config(commands={"tests": f'"{sys.executable}" -m pytest -q'}))
    run_hook("UserPromptSubmit", {"cwd": str(project), "prompt": "fix the addition bug"})
    stop = run_hook("Stop", {"cwd": str(project), "last_assistant_message": "fixed it"})
    assert stop.returncode == 2
    assert "UNVERIFIED" in stop.stderr
