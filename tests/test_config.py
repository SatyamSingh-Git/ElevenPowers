"""Configuration, profiles, and saying what is needed before the end.

The gate stopped 7 of 8 live runs on one model and 12 of 16 on another, and on
nearly all of them the work was already correct: the agent had done the job and
not shown it. Two things follow, and both are tested here. The obligations have
to be stated while there is still time to act on them, and a project has to be
able to say how much interruption it wants.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.config import DEFAULT_PROFILE, Config, load, save
from core.ledger import Ledger
from core.obligations import Claim
from core.report import guidance
from core.status import render

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_a_project_with_no_config_behaves_as_before(tmp_path):
    config = load(tmp_path)
    assert config.profile == DEFAULT_PROFILE
    assert config.blocks and config.speaks


def test_a_declared_profile_is_read(tmp_path):
    save(tmp_path, Config(profile="guide"))
    assert load(tmp_path).profile == "guide"
    assert not load(tmp_path).blocks


@pytest.mark.parametrize("profile,speaks,blocks", [
    ("off", False, False), ("guide", True, False), ("strict", True, True),
])
def test_what_each_profile_permits(tmp_path, profile, speaks, blocks):
    save(tmp_path, Config(profile=profile))
    config = load(tmp_path)
    assert (config.speaks, config.blocks) == (speaks, blocks)


def test_the_environment_overrides_a_committed_file(tmp_path, monkeypatch):
    save(tmp_path, Config(profile="strict"))
    monkeypatch.setenv("EP_PROFILE", "off")
    assert load(tmp_path).profile == "off"


def test_a_nonsense_profile_falls_back_rather_than_failing(tmp_path):
    (tmp_path / ".elevenpowers").mkdir()
    (tmp_path / ".elevenpowers" / "config.json").write_text('{"profile": "loud"}', encoding="utf-8")
    assert load(tmp_path).profile == DEFAULT_PROFILE


def test_unreadable_config_does_not_take_the_runtime_down(tmp_path):
    (tmp_path / ".elevenpowers").mkdir()
    (tmp_path / ".elevenpowers" / "config.json").write_text("{not json", encoding="utf-8")
    assert load(tmp_path).profile == DEFAULT_PROFILE


# --- a declared command is believed over a guess ----------------------------

def test_a_declared_test_command_means_the_project_has_tests(tmp_path):
    """Scanning cannot find a suite that lives behind a Makefile."""
    save(tmp_path, Config(commands={"tests": "make test"}))
    assert Ledger(root=tmp_path).surface.tests


def test_the_declared_command_is_what_gets_suggested(tmp_path):
    save(tmp_path, Config(commands={"tests": "make check"}))
    ledger = Ledger(root=tmp_path, request="fix the crash", claims=[Claim.BUG_FIXED])
    assert "make check" in guidance(ledger)


# --- guidance ---------------------------------------------------------------

def test_guidance_names_what_is_missing(tmp_path):
    """Each unmet obligation gets a line, and each line gets a way to meet it."""
    ledger = Ledger(root=tmp_path, request="fix the crash", claims=[Claim.BUG_FIXED])
    words = guidance(ledger)
    assert words.startswith("this task will need")
    assert len(words.splitlines()) >= 3


def test_guidance_is_silent_when_nothing_is_missing(tmp_path):
    assert guidance(Ledger(root=tmp_path)) == ""


# --- through the hook -------------------------------------------------------

def run_hook(event, payload):
    return subprocess.run(
        [sys.executable, "-m", "core.hook", event],
        input=json.dumps(payload), capture_output=True, text=True, cwd=REPO_ROOT,
    )


@pytest.fixture
def project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text("def test_x():\n    assert True\n",
                                                    encoding="utf-8")
    run_hook("UserPromptSubmit", {"cwd": str(tmp_path), "prompt": "fix the crash on upload"})
    return tmp_path


def edit(root):
    return run_hook("PostToolUse", {
        "cwd": str(root), "tool_name": "Edit",
        "tool_input": {"file_path": str(root / "src" / "app.py")},
        "tool_result": {"filePath": "x"},
    })


def context_of(result):
    if not result.stdout.strip():
        return ""
    return json.loads(result.stdout)["hookSpecificOutput"].get("additionalContext", "")


def test_the_first_edit_says_what_will_be_needed(project):
    assert "before it can be called done" in context_of(edit(project))


def test_it_says_so_once_and_then_stops(project):
    edit(project)
    assert context_of(edit(project)) == ""


def test_profile_off_says_nothing_at_all(project):
    save(project, Config(profile="off"))
    assert context_of(edit(project)) == ""
    stop = run_hook("Stop", {"cwd": str(project), "last_assistant_message": "done"})
    assert stop.returncode == 0 and not stop.stdout.strip()


def test_profile_guide_reports_without_blocking(project):
    save(project, Config(profile="guide"))
    stop = run_hook("Stop", {"cwd": str(project), "last_assistant_message": "done"})
    assert stop.returncode == 0
    assert "UNVERIFIED" in context_of(stop)


def test_profile_strict_still_blocks(project):
    stop = run_hook("Stop", {"cwd": str(project), "last_assistant_message": "done"})
    assert stop.returncode == 2


def test_the_block_records_which_obligation_was_unmet(project):
    run_hook("Stop", {"cwd": str(project), "last_assistant_message": "done"})
    decisions = json.loads((project / ".elevenpowers" / "ledger.json")
                           .read_text(encoding="utf-8"))["decisions"]
    blocked = [d for d in decisions if d["what"] == "gate blocked"]
    assert blocked and "suite_green" in blocked[-1]["why"]


# --- status -----------------------------------------------------------------

def test_status_on_an_untouched_directory(tmp_path):
    body = render(tmp_path)
    assert "profile   strict" in body and "standing aside" in body


def test_status_shows_the_open_task_and_what_is_missing(project):
    body = render(project)
    assert "bug_fixed" in body and "missing" in body and "UNVERIFIED" in body


def test_status_reports_declared_commands(project):
    save(project, Config(commands={"tests": "make test"}))
    assert "tests: make test" in render(project)
