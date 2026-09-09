"""Tests for what opens a claim, and what must not.

Claim inference is the switch that turns the whole runtime on. Getting it wrong
in one direction attaches obligations to a conversation; in the other it sits
out the task it exists for. Both directions are measured on 3,557 real turns by
`python -m eval.claims_run`; these pin the specific judgements.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.claims import infer, opens_new_task
from core.ledger import Ledger
from core.obligations import Claim
from core.parsers import written_paths

from eval.claim_cases import CASES

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_labelled_prompts(case):
    claims = [c.value for c in infer(case.prompt)]
    assert bool(claims) is case.should_claim, f"{case.name}: {case.why}"
    if case.claim:
        assert case.claim in claims, f"{case.name}: {case.why}"


@pytest.mark.parametrize("prompt", ["continue", "go on", "yes do it", "see this", "ans"])
def test_a_continuation_states_no_subject(prompt):
    assert not opens_new_task(prompt)


@pytest.mark.parametrize("prompt", [
    "what does this do?", "explain the auth flow", "fix the login bug",
])
def test_a_prompt_with_a_subject_of_its_own_replaces_the_task(prompt):
    assert opens_new_task(prompt)


def test_a_stack_trace_is_a_bug_report(tmp_path):
    """`read` in "cannot read property" used to rule the claim out."""
    assert Claim.BUG_FIXED in infer("TypeError: cannot read property id of undefined")


# --- claims that come from the work rather than the request -----------------

def ledger_after(tmp_path, request, path, body="x = 1\n"):
    target = tmp_path / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    ledger = Ledger(root=tmp_path, request=request)
    ledger.observe_edit(str(target))
    return ledger


def test_editing_source_opens_a_claim_when_the_prompt_stated_none(tmp_path):
    assert ledger_after(tmp_path, "continue", "src/app.py").claims == [Claim.FEATURE_ADDED]


def test_editing_prose_or_a_manifest_does_not(tmp_path):
    assert not ledger_after(tmp_path, "continue", "README.md", "# hi\n").claims
    assert not ledger_after(tmp_path, "continue", "package.json", "{}\n").claims


def test_a_question_is_not_turned_into_a_claim_by_an_edit(tmp_path):
    assert not ledger_after(tmp_path, "what does this module do?", "src/app.py").claims


def test_an_edit_records_the_file_either_way(tmp_path):
    ledger = ledger_after(tmp_path, "what does this module do?", "src/app.py")
    assert "src/app.py" in ledger.seen


def test_an_existing_claim_is_not_replaced(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    ledger = Ledger(root=tmp_path, request="fix the crash", claims=[Claim.BUG_FIXED])
    ledger.observe_edit(str(tmp_path / "src" / "app.py"))
    assert ledger.claims == [Claim.BUG_FIXED]


@pytest.mark.parametrize("command,expected", [
    ("cat > src/app.py", ["src/app.py"]),
    ("cat >> notes/log.txt", ["notes/log.txt"]),
    ("tee -a build/out.js", ["build/out.js"]),
    ("sed -i 's/a/b/' src/main.rs", ["src/main.rs"]),
    ("python -m pytest -q > /dev/null 2>&1", []),
    ("echo hi >&2", []),
    ("ls -la", []),
])
def test_shell_writes_are_recognised(command, expected):
    assert written_paths(command) == expected


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
    return tmp_path


def claims_of(root):
    path = root / ".elevenpowers" / "ledger.json"
    return json.loads(path.read_text(encoding="utf-8"))["claims"] if path.exists() else []


def test_a_continuation_does_not_clear_an_open_claim(project):
    run_hook("UserPromptSubmit", {"cwd": str(project), "prompt": "fix the crash on upload"})
    assert claims_of(project) == ["bug_fixed"]
    run_hook("UserPromptSubmit", {"cwd": str(project), "prompt": "continue"})
    assert claims_of(project) == ["bug_fixed"]


def test_a_new_question_does_clear_it(project):
    run_hook("UserPromptSubmit", {"cwd": str(project), "prompt": "fix the crash on upload"})
    run_hook("UserPromptSubmit", {"cwd": str(project), "prompt": "what does src/app.py do?"})
    assert claims_of(project) == []


def test_a_shell_write_opens_a_claim(project):
    run_hook("UserPromptSubmit", {"cwd": str(project), "prompt": "continue"})
    run_hook("PostToolUse", {
        "cwd": str(project), "tool_name": "Bash",
        "tool_input": {"command": "cat > src/app.py <<EOF\ny = 2\nEOF"},
        "tool_result": {"stdout": "", "stderr": "", "interrupted": False},
    })
    assert claims_of(project) == ["feature_added"]


def test_a_failed_shell_write_opens_nothing(project):
    run_hook("UserPromptSubmit", {"cwd": str(project), "prompt": "continue"})
    run_hook("PostToolUseFailure", {
        "cwd": str(project), "tool_name": "Bash",
        "tool_input": {"command": "cat > src/app.py"},
        "tool_result": "Error: Exit code 1\npermission denied\n",
    })
    assert claims_of(project) == []
