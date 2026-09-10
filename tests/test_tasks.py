"""The seeded-bug fixtures have to be exactly as broken as they claim.

A task where the hidden test already passes measures nothing, and a task whose
visible suite is red gives the agent the answer for free. Both failures are
silent: the run completes, a number comes out, and it means something other than
what it says. So each task is checked in both directions before any agent time is
spent on it.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from eval.live import build, verify
from eval.tasks import SUITES

ALL = SUITES["every"]


def run_pytest(target: Path, cwd: Path) -> int:
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(target), "-q"],
        cwd=cwd, capture_output=True, text=True, timeout=120,
    ).returncode


@pytest.fixture(params=ALL, ids=[t.name for t in ALL])
def seeded(request, tmp_path):
    build(request.param, tmp_path, arm="vanilla")
    return request.param, tmp_path


def test_the_visible_suite_is_green_on_the_broken_code(seeded):
    """Otherwise the agent is handed the diagnosis by a failing test."""
    task, root = seeded
    assert run_pytest(root / "tests", root) == 0, task.why


def test_the_hidden_test_fails_on_the_broken_code(seeded):
    """Otherwise the task cannot tell a real fix from no fix at all."""
    task, root = seeded
    assert not verify(task, root), task.why


def test_the_hidden_test_is_removed_after_checking(seeded):
    task, root = seeded
    verify(task, root)
    assert not (root / "tests" / "test_hidden.py").exists()


def test_every_task_reports_a_symptom_rather_than_a_fix(seeded):
    """A prompt naming the line to change measures nothing about verification."""
    task, _ = seeded
    lowered = task.prompt.lower()
    assert not any(word in lowered for word in ("weekday", "sorted(", "//", "kwargs")), \
        f"{task.name} gives away the diagnosis"


# --- the rule that decides whether a task can measure anything ---------------

REPO_TASKS = [t for t in SUITES["repo"] if t.naive]


@pytest.mark.parametrize("task", REPO_TASKS, ids=[t.name for t in REPO_TASKS])
def test_the_naive_fix_turns_the_visible_suite_red(task, tmp_path):
    """SWE-bench calls this PASS_TO_PASS: the tests a wrong fix must break.

    A task whose naive fix leaves the suite green cannot measure verification,
    because running the suite would not have helped. Both a weak and a strong
    model failed every such task identically.
    """
    build(task, tmp_path, arm="vanilla")
    assert run_pytest(tmp_path / "tests", tmp_path) == 0, "the suite starts green"
    rel, body = task.naive
    (tmp_path / rel).write_text(body, encoding="utf-8")
    assert run_pytest(tmp_path / "tests", tmp_path) != 0, task.why
