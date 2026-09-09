import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.scope import _singular, area, is_manifest, tokens, unrelated

from eval.scope_cases import CASES

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_labelled_scope_cases(case):
    reason = unrelated(case.target, case.seen, case.request, case.exists)
    assert bool(reason) is case.should_ask, f"{case.name}: {case.why}"


def test_area_treats_a_test_tree_as_mirroring_its_source_tree():
    assert area("tests/auth/test_session.py") == area("src/auth/session.py")


def test_area_separates_monorepo_packages():
    assert area("packages/api/src/handler.ts") != area("packages/web/src/app.tsx")


@pytest.mark.parametrize("word,expected", [
    ("dates", "date"), ("boxes", "box"), ("matches", "match"), ("entries", "entry"),
    ("status", "status"), ("analysis", "analysis"), ("session", "session"),
])
def test_singularisation(word, expected):
    assert _singular(word) == expected


def test_container_and_generic_words_carry_no_signal():
    assert tokens("packages/web/src/index.ts") == {"web"}
    assert tokens("src/billing/config.py") == {"billing"}


@pytest.mark.parametrize("name", [
    "package.json", "poetry.lock", "go.mod", "Cargo.toml", "Dockerfile", "yarn.lock",
])
def test_manifests_are_recognised(name):
    assert is_manifest(name)


def test_reason_names_the_area_and_offers_a_way_forward():
    reason = unrelated("src/billing/stripe.py", ["src/auth/session.py"],
                       "fix the session refresh", exists=True)
    assert "billing" in reason and "read it first" in reason


# --- through the hook ------------------------------------------------------

def run_hook(event, payload):
    return subprocess.run(
        [sys.executable, "-m", "core.hook", event],
        input=json.dumps(payload), capture_output=True, text=True, cwd=REPO_ROOT,
    )


@pytest.fixture
def project(tmp_path):
    for rel in ("src/auth/session.py", "src/billing/stripe.py", "pyproject.toml"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x = 1\n")
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", "b"]):
        subprocess.run(["git", *args], cwd=tmp_path, capture_output=True)
    run_hook("UserPromptSubmit", {"cwd": str(tmp_path), "prompt": "fix the session refresh bug"})
    run_hook("PostToolUse", {"cwd": str(tmp_path), "tool_name": "Read",
                             "tool_input": {"file_path": str(tmp_path / "src/auth/session.py")}})
    return tmp_path


def decision(result):
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)["hookSpecificOutput"].get("permissionDecision")


def test_editing_within_the_established_area_is_silent(project):
    r = run_hook("PreToolUse", {"cwd": str(project), "tool_name": "Edit",
                                "tool_input": {"file_path": str(project / "src/auth/session.py")}})
    assert decision(r) is None


def test_editing_an_unrelated_module_asks(project):
    r = run_hook("PreToolUse", {"cwd": str(project), "tool_name": "Edit",
                                "tool_input": {"file_path": str(project / "src/billing/stripe.py")}})
    assert decision(r) == "ask"


def test_creating_a_new_file_is_silent(project):
    r = run_hook("PreToolUse", {"cwd": str(project), "tool_name": "Write",
                                "tool_input": {"file_path": str(project / "src/auth/limiter.py")}})
    assert decision(r) is None


def test_manifest_edits_are_silent(project):
    r = run_hook("PreToolUse", {"cwd": str(project), "tool_name": "Edit",
                                "tool_input": {"file_path": str(project / "pyproject.toml")}})
    assert decision(r) is None


def test_reading_a_file_first_stops_the_question(project):
    target = str(project / "src/billing/stripe.py")
    assert decision(run_hook("PreToolUse", {"cwd": str(project), "tool_name": "Edit",
                                            "tool_input": {"file_path": target}})) == "ask"
    run_hook("PostToolUse", {"cwd": str(project), "tool_name": "Read",
                             "tool_input": {"file_path": target}})
    assert decision(run_hook("PreToolUse", {"cwd": str(project), "tool_name": "Edit",
                                            "tool_input": {"file_path": target}})) is None


def test_no_claim_means_no_scope_questions(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "b.py").write_text("y = 1\n")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, capture_output=True)
    run_hook("UserPromptSubmit", {"cwd": str(tmp_path), "prompt": "what does a.py do?"})
    run_hook("PostToolUse", {"cwd": str(tmp_path), "tool_name": "Read",
                             "tool_input": {"file_path": str(tmp_path / "a.py")}})
    r = run_hook("PreToolUse", {"cwd": str(tmp_path), "tool_name": "Edit",
                                "tool_input": {"file_path": str(tmp_path / "b.py")}})
    assert decision(r) is None


def test_the_question_is_recorded_as_a_decision(project):
    run_hook("PreToolUse", {"cwd": str(project), "tool_name": "Edit",
                            "tool_input": {"file_path": str(project / "src/billing/stripe.py")}})
    ledger = json.loads((project / ".elevenpowers" / "ledger.json").read_text())
    assert any(d["what"] == "scope question" for d in ledger["decisions"])
