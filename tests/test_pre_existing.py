"""A failure is pre-existing only when something shows it was there before the task.

FeatureArc (arXiv 2610.37434) found agents calling a red self-test "unrelated or
pre-existing" in 321 of 367 stages, and checking that on the starting code in 23.
The ledger used to take the task's first sighting of a test as its state before the
task, so a test the agent itself broke, run twice after the edit, came out VERIFIED
with the failure listed as pre-existing - the excuse, certified. Two things now
show it: the test failing on the tree the task opened before the task edited
anything, or failing when the runtime runs it on that tree itself (uncommitted
work included). Nothing else does, and an unshown failure is named, not excused.
"""
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from core.evidence import Evidence, Kind, Result, source_files, tree_hash, vcs_state
from core.ledger import Ledger, Status
from core.obligations import Claim, Risk
from core.report import end_report, gate_message

REPO_ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_auth.py::test_login"


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "auth.py").write_text("def login():\n    return True\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_auth.py").write_text("def test_login():\n    assert True\n")
    return tmp_path


def _red_twice(repo, first_vcs="after", edited_between=True, **fields):
    """The suite run twice, red on the same test both times, with an edit between them."""
    files = source_files(repo)
    tree = tree_hash(repo, files)
    now = time.time()
    led = Ledger(root=repo, claims=[Claim.FEATURE_ADDED], risk=Risk.LOW, opened_vcs="opening",
                 first_edit_at=now - 5 if edited_between else now - 20, **fields)
    led.touched = ["src/auth.py"]
    for at, vcs in ((now - 10, first_vcs), (now, "after")):
        led.add([
            Evidence(Kind.SUITE, "tests", Result.FAIL, files, tree, passed=1, failed=1, counted=True,
                     at=at, vcs=vcs),
            Evidence(Kind.TEST, TEST, Result.FAIL, files, tree, at=at, vcs=vcs),
        ])
    return led


def test_a_failure_first_seen_after_the_change_is_not_pre_existing(repo):
    led = _red_twice(repo)
    assert led.pre_existing() == []
    assert led.status() is Status.UNVERIFIED
    assert "pre-existing" not in end_report(led)
    told = gate_message(led)
    assert TEST in told and "not shown to predate this task" in told


def test_a_failure_seen_on_the_opened_tree_before_any_edit_is_pre_existing(repo):
    led = _red_twice(repo, first_vcs="opening")
    assert TEST in [e.identity for e in led.pre_existing()]
    assert led.status() is Status.VERIFIED


def test_the_opened_tree_after_an_edit_git_cannot_see_proves_nothing(repo):
    """An edit to an ignored file leaves the fingerprint alone; the edit's time does not."""
    led = _red_twice(repo, first_vcs="opening", edited_between=False)
    assert led.pre_existing() == []
    assert led.status() is not Status.VERIFIED


def test_a_failure_red_on_the_opened_tree_when_asked_is_pre_existing(repo):
    led = _red_twice(repo, at_open={TEST: True})
    assert TEST in [e.identity for e in led.pre_existing()]
    assert led.status() is Status.VERIFIED


def test_a_failure_green_on_the_opened_tree_is_named_not_accused(repo):
    led = _red_twice(repo, at_open={TEST: False})
    assert led.pre_existing() == []
    assert led.status() is Status.UNVERIFIED
    told = gate_message(led)
    assert TEST in told and "passing when this task opened" in told


def test_a_red_sighting_before_any_edit_outranks_a_green_answer(repo):
    """A flaky test seen red before the task touched anything is given the benefit."""
    led = _red_twice(repo, first_vcs="opening", at_open={TEST: False})
    assert TEST in [e.identity for e in led.pre_existing()]


def test_a_later_green_suite_clears_an_earlier_red_test(repo):
    """`pytest -q` names failures but prints passes as dots, so the green run names nothing."""
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.FEATURE_ADDED], risk=Risk.LOW)
    led.add([
        Evidence(Kind.SUITE, "tests", Result.FAIL, files, tree, passed=1, failed=1, counted=True, at=1.0),
        Evidence(Kind.TEST, TEST, Result.FAIL, files, tree, at=1.0),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, passed=2, counted=True, at=2.0),
    ])
    assert led.failing_now() == []
    assert led.status() is Status.VERIFIED
    assert TEST not in end_report(led)


def test_a_later_green_run_of_one_file_does_not_clear_a_test_elsewhere(repo):
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.FEATURE_ADDED], risk=Risk.LOW)
    led.add([
        Evidence(Kind.TEST, TEST, Result.FAIL, files, tree, at=1.0),
        Evidence(Kind.SUITE, "tests/test_other.py", Result.PASS, files, tree, passed=3, counted=True,
                 command="python -m pytest tests/test_other.py", at=2.0),
    ])
    assert [e.identity for e in led.failing_now()] == [TEST]


def test_a_test_in_a_file_the_task_touched_is_not_asked_on_the_opened_tree(repo, monkeypatch):
    from core import review, stress
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, task="t-1", claims=[Claim.FEATURE_ADDED], risk=Risk.LOW, opened_commit="abc")
    led._config = replace(led.config, commands={"tests": "python -m pytest"})
    led.add([Evidence(Kind.TEST, TEST, Result.FAIL, files, tree, at=time.time())])
    asked = []
    monkeypatch.setattr(review, "_worktree", contextmanager(lambda root, commit: iter([(repo, repo, repo)])))
    monkeypatch.setattr(review, "_run", lambda *a, **k: asked.append(a) or
                        {"problem": "", "failing": [], "passed": []})
    led.touched = ["src/auth.py"]
    assert stress.already_failing(led) is True and len(asked) == 1     # the forward control: it is asked
    led.at_open.clear()
    asked.clear()
    led.touched = ["src/auth.py", "tests/test_auth.py"]
    assert stress.already_failing(led) is False
    assert asked == []


def test_no_fingerprint_proves_nothing(repo):
    """Outside git both fingerprints are empty, and equal empties are not the same tree."""
    led = _red_twice(repo, first_vcs="")
    led.opened_vcs = ""
    for e in led.evidence:
        e.vcs = ""
    assert led.pre_existing() == []
    assert led.status() is not Status.VERIFIED


def test_the_opened_state_survives_a_save(repo):
    led = Ledger(root=repo, task="t-1", opened_vcs="opening", opened_commit="abc", first_edit_at=3.0,
                 at_open={TEST: True})
    led.save()
    back = Ledger.load(repo)
    assert (back.opened_vcs, back.opened_commit, back.first_edit_at, back.at_open) == \
        ("opening", "abc", 3.0, {TEST: True})


def test_an_edit_records_when_the_task_first_changed_something(repo):
    led = Ledger(root=repo, request="add a thing")
    led.observe_edit(str(repo / "src" / "auth.py"))
    first = led.first_edit_at
    assert first > 0
    led.observe_edit(str(repo / "tests" / "test_auth.py"))
    assert led.first_edit_at == first


def test_what_a_test_run_writes_does_not_move_the_tree_fingerprint(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "-c", "user.email=p@example.com", "-c", "user.name=p", "commit", "-q", "-m", "base")
    opening = vcs_state(tmp_path)
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "app.cpython-313.pyc").write_bytes(b"\x00")
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".pytest_cache" / "README.md").write_text("cache\n", encoding="utf-8")
    assert vcs_state(tmp_path) == opening
    (tmp_path / "new.py").write_text("y = 2\n", encoding="utf-8")
    assert vcs_state(tmp_path) != opening
    # A real package called build is source, not output.
    (tmp_path / "src" / "build").mkdir(parents=True)
    (tmp_path / "src" / "build" / "__init__.py").write_text("z = 3\n", encoding="utf-8")
    with_new = vcs_state(tmp_path)
    (tmp_path / "src" / "build" / "more.py").write_text("w = 4\n", encoding="utf-8")
    assert vcs_state(tmp_path) != with_new


# --- through the hook, with git and a real pytest ------------------------------------

CALC_TEST = ("import pathlib, sys\nsys.path.insert(0, str(pathlib.Path(__file__).parents[1] / 'src'))\n"
             "from calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n\n\n"
             "def test_other():\n    assert True\n")


def _hook(event, payload, env=None):
    return subprocess.run([sys.executable, "-m", "core.hook", event], input=json.dumps(payload),
                          capture_output=True, text=True, cwd=REPO_ROOT, env=env)


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _project(repo, *, red_on_base, discoverable, ignore_caches=True, sub="", test_body=CALC_TEST):
    """A git repository holding the project at `repo/sub`; returns the project folder."""
    root = repo / sub if sub else repo
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "calc.py").write_text(
        f"def add(a, b):\n    return {'a - b' if red_on_base else 'a + b'}\n", encoding="utf-8")
    (root / "tests" / "test_calc.py").write_text(test_body, encoding="utf-8")
    if ignore_caches:
        (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n", encoding="utf-8")
    if discoverable:
        (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "probe@example.com")
    _git(repo, "config", "user.name", "probe")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return root


def _open(root, env=None):
    _hook("UserPromptSubmit", {"cwd": str(root), "prompt": "add a subtract function to src/calc.py"}, env)


def _run_tests(root, env=None):
    done = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=root, capture_output=True, text=True,
                          env=env)
    _hook("PostToolUse", {"cwd": str(root), "tool_name": "Bash",
                          "tool_input": {"command": "python -m pytest -q"},
                          "tool_response": {"stdout": done.stdout + done.stderr, "stderr": "",
                                            "interrupted": False, "returnCode": done.returncode}}, env)


def _write(root, rel, body, env=None):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    _hook("PostToolUse", {"cwd": str(root), "tool_name": "Write",
                          "tool_input": {"file_path": str(path), "content": body},
                          "tool_response": {"filePath": str(path)}}, env)


def _break_add(root, env=None):
    _write(root, "src/calc.py", "def add(a, b):\n    return a - b\n\n\ndef subtract(a, b):\n    return a - b\n", env)


def _add_subtract(root, env=None):
    _write(root, "src/calc.py", (root / "src" / "calc.py").read_text(encoding="utf-8")
           + "\n\ndef subtract(a, b):\n    return a - b\n", env)


def _stop(root, env=None):
    return _hook("Stop", {"cwd": str(root), "stop_hook_active": False,
                          "last_assistant_message": "Added subtract(). test_add fails, but that "
                                                    "failure is pre-existing and unrelated."}, env)


def _ledger(root):
    return json.loads((root / ".elevenpowers" / "ledger.json").read_text(encoding="utf-8"))


def test_through_the_hook_a_test_the_agent_broke_is_not_excused(tmp_path):
    root = _project(tmp_path, red_on_base=False, discoverable=True)
    _open(root)
    _break_add(root)
    _run_tests(root)
    _run_tests(root)
    done = _stop(root)
    assert done.returncode == 2, done.stdout
    assert "tests/test_calc.py::test_add" in done.stderr and "passing when this task opened" in done.stderr
    assert _ledger(root)["at_open"] == {"tests/test_calc.py::test_add": False}


def test_through_the_hook_a_test_red_before_the_task_is_still_excused(tmp_path):
    root = _project(tmp_path, red_on_base=True, discoverable=True)
    _open(root)
    _add_subtract(root)
    _run_tests(root)
    _run_tests(root)
    done = _stop(root)
    assert done.returncode == 0, done.stderr
    assert "VERIFIED" in done.stdout and "pre-existing failures" in done.stdout
    assert "tests" not in _ledger(root)["discrimination"]


def test_through_the_hook_uncommitted_work_that_broke_a_test_is_not_the_tasks(tmp_path):
    root = _project(tmp_path, red_on_base=False, discoverable=True)
    (root / "src" / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    _open(root)
    _write(root, "src/extra.py", "def subtract(a, b):\n    return a - b\n")
    _run_tests(root)
    _run_tests(root)
    done = _stop(root)
    assert done.returncode == 0, done.stderr
    assert "pre-existing failures" in done.stdout


def test_through_the_hook_a_new_test_the_agent_wrote_is_not_pre_existing(tmp_path):
    root = _project(tmp_path, red_on_base=False, discoverable=True)
    _open(root)
    _add_subtract(root)
    _write(root, "tests/test_subtract.py",
           "import pathlib, sys\nsys.path.insert(0, str(pathlib.Path(__file__).parents[1] / 'src'))\n\n\n"
           "def test_subtract():\n    from calc import subtract\n    assert subtract(5, 3) == 3\n")
    _run_tests(root)
    _run_tests(root)
    done = _stop(root)
    assert done.returncode == 2, done.stdout
    assert "tests/test_subtract.py::test_subtract" in done.stderr


def test_through_the_hook_an_old_tree_importing_the_checkout_proves_nothing(tmp_path):
    """With PYTHONPATH pointing into the project, the old tree would test the agent's code."""
    root = _project(tmp_path, red_on_base=False, discoverable=True,
                    test_body="from calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n")
    env = {**os.environ, "PYTHONPATH": str(root / "src")}
    _open(root, env)
    _break_add(root, env)
    _run_tests(root, env)
    _run_tests(root, env)
    done = _stop(root, env)
    assert done.returncode == 2, done.stdout
    assert "pre-existing failures" not in done.stdout + done.stderr
    assert _ledger(root)["at_open"] == {"tests/test_calc.py::test_add": None}


def test_through_the_hook_a_project_in_a_subfolder_is_asked_in_its_folder(tmp_path):
    root = _project(tmp_path, red_on_base=True, discoverable=True, sub="pkg")
    _open(root)
    _add_subtract(root)
    _run_tests(root)
    _run_tests(root)
    done = _stop(root)
    assert done.returncode == 0, done.stderr
    assert "pre-existing failures" in done.stdout
    assert _ledger(root)["at_open"] == {"tests/test_calc.py::test_add": True}


def test_through_the_hook_a_teardown_error_already_red_is_still_excused(tmp_path):
    body = ("import pytest\n\n\n@pytest.fixture\ndef res():\n    yield 1\n"
            "    raise PermissionError('cannot remove tmp')\n\n\n"
            "def test_cleanup(res):\n    assert res == 1\n\n\ndef test_other():\n    assert True\n")
    root = _project(tmp_path, red_on_base=False, discoverable=True, test_body=body)
    _open(root)
    _add_subtract(root)
    _run_tests(root)
    _run_tests(root)
    done = _stop(root)
    assert done.returncode == 0, done.stderr
    assert "pre-existing failures" in done.stdout


def test_the_opened_tree_is_asked_once_per_test(tmp_path, monkeypatch):
    from core import review, stress
    root = _project(tmp_path, red_on_base=False, discoverable=True)
    _open(root)
    _break_add(root)
    _run_tests(root)
    _stop(root)
    asked = []
    monkeypatch.setattr(review, "_run", lambda *a, **k: asked.append(a))
    assert stress.already_failing(Ledger.load(root)) is False
    assert asked == []


@pytest.mark.parametrize("ignore_caches", [True, False])
def test_through_the_hook_a_run_before_the_edit_shows_it_without_a_test_command(tmp_path, ignore_caches):
    root = _project(tmp_path, red_on_base=True, discoverable=False, ignore_caches=ignore_caches)
    _open(root)
    _run_tests(root)
    _add_subtract(root)
    _run_tests(root)
    done = _stop(root)
    assert done.returncode == 0, done.stderr
    assert "pre-existing failures" in done.stdout


def test_through_the_hook_a_run_only_after_the_edit_shows_nothing_without_a_test_command(tmp_path):
    root = _project(tmp_path, red_on_base=True, discoverable=False)
    _open(root)
    _add_subtract(root)
    _run_tests(root)
    _run_tests(root)
    done = _stop(root)
    assert done.returncode == 2, done.stdout
    assert "not shown to predate this task" in done.stderr
