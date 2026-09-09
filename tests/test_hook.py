import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.claims import infer
from core.ledger import Ledger
from core.obligations import Claim


def run_hook(event, payload, cwd):
    return subprocess.run(
        [sys.executable, "-m", "core.hook", event],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=Path(__file__).resolve().parents[1],
        env={"PATH": ""} | dict(__import__("os").environ),
    )


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "auth.py").write_text("x = 1\n")
    return tmp_path


@pytest.mark.parametrize("request_text,expected", [
    ("fix the intermittent auth race condition", [Claim.BUG_FIXED]),
    ("add SSO support for organizations", [Claim.FEATURE_ADDED]),
    ("rename the User model to Account", [Claim.REFACTOR_SAFE]),
    ("add a migration for the sessions table", [Claim.MIGRATION_SAFE]),
    ("make the dashboard query faster", [Claim.PERF_IMPROVED]),
    ("upgrade the react dependency to v19", [Claim.DEPS_UPDATED]),
    ("fix a typo in the README", [Claim.BUG_FIXED]),
    ("update the changelog wording", [Claim.DOCS_CHANGED]),
])
def test_claim_inference(request_text, expected):
    assert infer(request_text) == expected


@pytest.mark.parametrize("request_text", [
    "what does the auth module do?",
    "explain how sessions work",
    "review this design for me",
    "",
])
def test_questions_and_reading_produce_no_claim(request_text):
    assert infer(request_text) == []


def test_prompt_hook_writes_ledger_and_banner(repo):
    result = run_hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "fix the auth race"}, repo)
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert "claims: bug_fixed" in out["hookSpecificOutput"]["additionalContext"]
    assert Ledger.load(repo).claims == [Claim.BUG_FIXED]


def test_question_prompt_leaves_no_claims(repo):
    run_hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "what does auth.py do?"}, repo)
    assert Ledger.load(repo).claims == []


def test_post_tool_captures_test_evidence(repo):
    run_hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "fix the auth race"}, repo)
    run_hook("PostToolUse", {
        "cwd": str(repo),
        "tool_name": "Bash",
        "tool_input": {"command": "pytest tests/"},
        "tool_response": {"stdout": "=== 2 passed in 0.1s ===", "exit_code": 0},
    }, repo)
    assert len(Ledger.load(repo).evidence) >= 1


def test_stop_blocks_when_unverified(repo):
    run_hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "fix the auth race"}, repo)
    result = run_hook("Stop", {"cwd": str(repo)}, repo)
    assert result.returncode == 2
    assert "UNVERIFIED" in result.stderr and "missing" in result.stderr


def test_stop_passes_when_no_claim(repo):
    run_hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "what is in auth.py?"}, repo)
    assert run_hook("Stop", {"cwd": str(repo)}, repo).returncode == 0


def test_stop_gives_up_after_max_blocks(repo):
    run_hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "fix the auth race"}, repo)
    codes = [run_hook("Stop", {"cwd": str(repo)}, repo).returncode for _ in range(4)]
    assert codes[:2] == [2, 2] and codes[2] == 0


def test_full_cycle_reaches_verified(repo):
    run_hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "fix the auth race"}, repo)
    out = "tests/test_auth.py::test_race PASSED\n=== 1 passed in 0.1s ===\n"
    run_hook("PostToolUse", {
        "cwd": str(repo), "tool_name": "Bash",
        "tool_input": {"command": "pytest tests/test_auth.py"},
        "tool_response": {"stdout": out, "exit_code": 0},
    }, repo)
    result = run_hook("Stop", {"cwd": str(repo)}, repo)
    assert result.returncode == 0
    assert "VERIFIED" in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_edit_after_green_blocks_again_as_stale(repo):
    run_hook("UserPromptSubmit", {"cwd": str(repo), "prompt": "fix the auth race"}, repo)
    out = "tests/test_auth.py::test_race PASSED\n=== 1 passed in 0.1s ===\n"
    run_hook("PostToolUse", {
        "cwd": str(repo), "tool_name": "Bash",
        "tool_input": {"command": "pytest tests/test_auth.py"},
        "tool_response": {"stdout": out, "exit_code": 0},
    }, repo)
    assert run_hook("Stop", {"cwd": str(repo)}, repo).returncode == 0
    (repo / "src" / "auth.py").write_text("x = 2\n")
    result = run_hook("Stop", {"cwd": str(repo)}, repo)
    assert result.returncode == 2
    assert "stale" in result.stderr and "re-run" in result.stderr


def test_scope_guard_asks_outside_allowed_paths(repo):
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], allow=["src/auth/**"])
    led.save()
    result = run_hook("PreToolUse", {
        "cwd": str(repo), "tool_name": "Edit",
        "tool_input": {"file_path": str(repo / "src" / "billing.py")},
    }, repo)
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_destructive_command_asks(repo):
    result = run_hook("PreToolUse", {
        "cwd": str(repo), "tool_name": "Bash",
        "tool_input": {"command": "rm -rf / --no-preserve-root"},
    }, repo)
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_ordinary_command_is_untouched(repo):
    result = run_hook("PreToolUse", {
        "cwd": str(repo), "tool_name": "Bash", "tool_input": {"command": "pytest -q"},
    }, repo)
    assert result.stdout.strip() == "" and result.returncode == 0
