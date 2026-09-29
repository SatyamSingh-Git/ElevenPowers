"""One completion allowance, durable baselines, and honest confirmation receipts."""
import subprocess
import os
import sys
import time
from dataclasses import replace

import pytest

from core import hook, jobs, stress
from core.config import Config, save as save_config
from core.evidence import Evidence, Freshness, Kind, Result, source_files, tree_hash
from core.ledger import Ledger
from core.obligations import Claim


def ledger(tmp_path, profile="guide"):
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_app.py").write_text("def test_x():\n    assert True\n", encoding="utf-8")
    command = f'"{sys.executable}" -m pytest tests -q'
    config = Config(profile=profile, commands={"tests": command}, auto_detect=False)
    save_config(tmp_path, config)
    observed = source_files(tmp_path)
    return Ledger(root=tmp_path, task="shared-budget", base="base", request="refactor app",
                  claims=[Claim.REFACTOR_SAFE], _config=config,
                  evidence=[Evidence(kind=Kind.SUITE, identity="tests", result=Result.PASS,
                                     observed=observed, tree=tree_hash(tmp_path, observed),
                                     command=command, counted=True, passed=1)])


def test_transient_baseline_failure_is_retried(tmp_path, monkeypatch):
    led = ledger(tmp_path)
    outcomes = iter([None, (True, "1 passed")])
    monkeypatch.setattr(stress, "on_the_old_tree", lambda *a, **k: next(outcomes))
    led.discrimination, led.failed_before = stress.stress(led)
    assert led.discrimination == {"tests": stress.UNCHECKABLE}
    led.discrimination, led.failed_before = stress.stress(led)
    assert led.discrimination == {"tests": stress.VACUOUS}


def test_completed_baseline_is_saved_before_caller_returns(tmp_path, monkeypatch):
    led = ledger(tmp_path)
    monkeypatch.setattr(stress, "on_the_old_tree", lambda *a, **k: (True, "1 passed"))
    stress.stress(led)
    saved = Ledger.load(tmp_path)
    assert saved.discrimination == {"tests": stress.VACUOUS}
    assert saved.discrimination_inputs.get("tests")


def test_changed_baseline_inputs_clear_old_identities_before_retry(tmp_path, monkeypatch):
    led = ledger(tmp_path)
    led.touched = ["tests/test_app.py"]
    monkeypatch.setattr(stress, "on_the_old_tree", lambda *a, **k:
                        (False, "FAILED tests/test_app.py::test_x - assert False"))
    led.discrimination, led.failed_before = stress.stress(led)
    assert led.failed_before == ["tests/test_app.py::test_x"]
    (tmp_path / "tests/test_app.py").write_text("def test_x():\n    assert 1 == 1\n", encoding="utf-8")

    def retried(*args, **kwargs):
        saved = Ledger.load(tmp_path)
        assert saved.failed_before == []
        assert saved.passed_before == []
        assert not saved.discrimination_inputs.get("tests")
        return None

    monkeypatch.setattr(stress, "on_the_old_tree", retried)
    assert stress.stress(led)[1] == []


def test_exhausted_baseline_is_journaled_without_preparation(tmp_path, monkeypatch):
    led = ledger(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail("exhausted baseline launched a process")
    monkeypatch.setattr(stress.process, "run", forbidden)
    with jobs.Session(tmp_path, led.task, seconds=0):
        assert stress.on_the_old_tree(tmp_path, "base", "not-started") is None
    assert any(c["phase"] == "baseline" and c["status"] == "deferred"
               for c in jobs.read(tmp_path)["checks"])


def test_carried_test_changed_during_baseline_is_not_cached(tmp_path, monkeypatch):
    led = ledger(tmp_path)
    led.touched = ["tests/test_app.py"]

    def edited_during_run(*args, **kwargs):
        (tmp_path / "tests/test_app.py").write_text("def test_x():\n    assert False\n", encoding="utf-8")
        return False, "FAILED tests/test_app.py::test_x - assert False"

    monkeypatch.setattr(stress, "on_the_old_tree", edited_during_run)
    verdicts, red = stress.stress(led)
    assert verdicts == {"tests": stress.UNCHECKABLE}
    assert red == []
    assert not led.discrimination_inputs.get("tests")
    assert led.passed_before == []


def test_restored_old_mtime_does_not_hide_carried_test_mutation(tmp_path, monkeypatch):
    led = ledger(tmp_path)
    led.touched = ["tests/test_app.py"]
    target = tmp_path / "tests/test_app.py"
    target.write_text("def test_x():\n    assert 1\n", encoding="utf-8")
    old = time.time() - 60
    os.utime(target, (old, old))
    initial_stat = target.stat()

    def replaced(*args, **kwargs):
        target.write_text("def test_x():\n    assert 0\n", encoding="utf-8")
        os.utime(target, ns=(initial_stat.st_atime_ns, initial_stat.st_mtime_ns))
        return False, "FAILED tests/test_app.py::test_x - assert 0"

    monkeypatch.setattr(stress, "on_the_old_tree", replaced)
    verdicts, red = stress.stress(led)
    assert verdicts == {"tests": stress.UNCHECKABLE}
    assert red == []
    assert not led.discrimination_inputs.get("tests")


def test_baseline_setup_uses_remaining_budget_and_cleanup_has_reserve(tmp_path, monkeypatch):
    led = ledger(tmp_path)
    launches = []

    def run(command, *, cwd, timeout, shell=True):
        launches.append((command, timeout))
        if command[:3] == ["git", "worktree", "add"]:
            jobs.current().budget.deadline = time.monotonic() - .01
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(stress.process, "run", run)
    with jobs.Session(tmp_path, led.task, seconds=2):
        assert stress.on_the_old_tree(tmp_path, "base", "should-not-run") is None
    assert len(launches) == 2
    assert launches[0][0][:3] == ["git", "worktree", "add"]
    assert 0 < launches[0][1] <= 2
    assert launches[1][0][:3] == ["git", "worktree", "remove"]
    assert 0 < launches[1][1] <= 10
    assert any(c["phase"] == "baseline" and c["status"] == "deferred"
               for c in jobs.read(tmp_path)["checks"])


def test_confirmation_cannot_certify_an_edit_during_the_run(tmp_path):
    led = ledger(tmp_path)
    led.failed_before = ["tests/test_app.py::test_x"]
    (tmp_path / "tests/test_app.py").write_text(
        "from pathlib import Path\ndef test_x():\n"
        "    Path('app.py').write_text('value = 2\\n')\n", encoding="utf-8")
    found = stress.confirm(led)
    assert not any(e.freshness(tmp_path) is Freshness.FRESH for e in found)
    assert not any(d["what"] == stress.CONFIRMED for d in led.decisions)
    assert jobs.read(tmp_path)["checks"][-1]["status"] == "stale"


def test_confirmation_retries_after_previously_confirmed_source_changes(tmp_path):
    led = ledger(tmp_path)
    led.failed_before = ["tests/test_app.py::test_x"]
    first = stress.confirm(led)
    assert first
    led.add(first)
    (tmp_path / "app.py").write_text("value = 2\n", encoding="utf-8")
    second = stress.confirm(led)
    assert second, "a historical confirmation decision suppressed fresh execution"
    assert all(e.freshness(tmp_path) is Freshness.FRESH for e in second)


@pytest.mark.parametrize("result", [Result.FAIL, Result.ERROR])
def test_newer_nonpass_prevents_reuse_of_historical_confirmation(tmp_path, result):
    led = ledger(tmp_path)
    led.failed_before = ["tests/test_app.py::test_x"]
    first = stress.confirm(led)
    assert first
    led.add(first)
    led.add([replace(first[0], result=result, at=first[0].at + .001,
                     execution="incomplete" if result is Result.ERROR else "complete")])
    assert stress.confirm(led), "historical PASS hid a newer failed or incomplete receipt"


@pytest.mark.parametrize("interruption", [subprocess.TimeoutExpired("test", 1), KeyboardInterrupt()])
def test_confirmation_persists_incomplete_receipt_before_interruption(tmp_path, monkeypatch, interruption):
    led = ledger(tmp_path)
    led.failed_before = ["tests/test_app.py::test_x"]
    led.add([replace(led.evidence[0], kind=Kind.TEST, identity="tests/test_app.py::test_x",
                     command="an older targeted command", at=time.time() - 10)])

    def interrupted(*args, **kwargs):
        saved = Ledger.load(tmp_path)
        records = [e for e in saved.evidence if e.kind is Kind.TEST]
        assert records, "execution started before durable provisional receipt"
        latest = max(records, key=lambda e: e.at)
        assert latest.execution == "incomplete"
        assert latest.identity == "tests/test_app.py::test_x"
        raise interruption

    monkeypatch.setattr(jobs, "execute", interrupted)
    if isinstance(interruption, KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            stress.confirm(led)
    else:
        assert stress.confirm(led) == []
    assert Ledger.load(tmp_path).evidence[-1].execution == "incomplete"


def test_confirmation_persists_completed_receipt_without_caller_add(tmp_path):
    led = ledger(tmp_path)
    led.failed_before = ["tests/test_app.py::test_x"]
    found = stress.confirm(led)
    saved = Ledger.load(tmp_path)
    assert found
    assert any(e.kind is Kind.TEST and e.identity == found[0].identity
               and e.result is Result.PASS and e.execution == "complete"
               for e in saved.evidence)
    latest = max((e for e in saved.evidence if e.kind is Kind.TEST), key=lambda e: e.at)
    assert latest.result is Result.PASS and latest.at > 0


def test_confirmation_receipt_is_bound_to_original_declaration(tmp_path):
    led = ledger(tmp_path)
    led.failed_before = ["tests/test_app.py::test_x"]
    found = stress.confirm(led)
    assert found and found[0].freshness(tmp_path) is Freshness.FRESH
    save_config(tmp_path, Config(profile="guide", auto_detect=False,
                                 commands={"tests": led.config.commands["tests"] + " -v"}))
    assert found[0].freshness(tmp_path) is Freshness.STALE


def test_stop_reports_task_rollover_without_claiming_completion(tmp_path, monkeypatch, capsys):
    led = ledger(tmp_path)
    led.evidence = []
    led.save()

    def changed(*args):
        raise jobs.Superseded("a newer task replaced this verification attempt")

    monkeypatch.setattr(hook, "discharge", changed)
    assert hook.on_stop({"last_assistant_message": "done"}, tmp_path) == 0
    output = capsys.readouterr().out
    assert "UNVERIFIED" in output and "task changed" in output


def test_incomplete_coverage_does_not_certify_confirmation(tmp_path, monkeypatch):
    led = ledger(tmp_path)
    led.failed_before = ["tests/test_app.py::test_x"]
    config = Config(profile="guide", commands=led.config.commands,
                    scan={"max_files": 1}, auto_detect=False)
    save_config(tmp_path, config)
    led._config = config
    def forbidden(*args, **kwargs):
        pytest.fail("confirmation launched without complete source coverage")
    monkeypatch.setattr(jobs, "execute", forbidden)
    found = stress.confirm(led)
    assert not any(e.freshness(tmp_path) is Freshness.FRESH for e in found)
    assert not any(d["what"] == stress.CONFIRMED for d in led.decisions)


def test_stop_owns_one_session_across_all_three_phases(tmp_path, monkeypatch):
    led = ledger(tmp_path)
    led.evidence = []
    led.save()
    seen = []

    def phase(result):
        def run(*args):
            seen.append(jobs.current())
            return result
        return run

    monkeypatch.setattr(hook, "discharge", phase([]))
    monkeypatch.setattr(hook, "stress", phase(({}, [])))
    monkeypatch.setattr(hook, "confirm", phase([]))
    hook.on_stop({"last_assistant_message": "done"}, tmp_path)
    assert len(seen) == 3
    assert seen[0] is not None, "stop did not own the verification session"
    assert all(session is seen[0] for session in seen)
    assert jobs.current() is None


def test_stop_reloads_task_after_acquiring_ownership(tmp_path, monkeypatch):
    led = ledger(tmp_path)
    led.evidence = []
    led.save()
    original_session = jobs.Session

    class ChangedBeforeLockReturned(original_session):
        def __enter__(self):
            session = super().__enter__()
            session.queue("old task check", "old command")
            newer = Ledger.load(tmp_path)
            newer.task = "new-task"
            newer.request = "refactor the newly opened task"
            newer.save()
            return session

    seen = []

    def discharge(current):
        seen.append((current.task, current.request, jobs.current().task))
        return []

    monkeypatch.setattr(jobs, "Session", ChangedBeforeLockReturned)
    monkeypatch.setattr(hook, "discharge", discharge)
    monkeypatch.setattr(hook, "stress", lambda *a: ({}, []))
    monkeypatch.setattr(hook, "confirm", lambda *a: [])
    hook.on_stop({"last_assistant_message": "done"}, tmp_path)
    assert seen == [("new-task", "refactor the newly opened task", "new-task")]
    saved = jobs.read(tmp_path)
    assert saved["task"] == "new-task"
    assert not any(c["phase"] == "old task check" for c in saved["checks"])


def test_busy_stop_never_reports_verified_or_runs_commands(tmp_path, monkeypatch, capsys):
    led = ledger(tmp_path)
    led.save()

    def forbidden(*args):
        pytest.fail("busy stop launched work")

    monkeypatch.setattr(hook, "stress", forbidden)
    monkeypatch.setattr(hook, "snapshot", forbidden)
    with jobs.Session(tmp_path, led.task):
        hook.on_stop({"last_assistant_message": "done"}, tmp_path)
    output = capsys.readouterr().out
    assert "already running" in output
    assert "UNVERIFIED" in output


def test_off_stop_does_not_create_session_or_run_work(tmp_path, monkeypatch):
    led = ledger(tmp_path, "off")
    led.save()

    def forbidden(*args, **kwargs):
        pytest.fail("off profile started work")

    monkeypatch.setattr(jobs, "Session", forbidden)
    monkeypatch.setattr(hook, "_changed_paths", forbidden)
    hook.on_stop({"last_assistant_message": "done"}, tmp_path)
    assert not (tmp_path / ".elevenpowers/verification.json").exists()
