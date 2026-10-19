"""Declared-check feedback delivery is observed without claiming model use."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from core.check_feedback import feedback
from core.config import Config, save
from core.hosts import readiness, transport
from core.hosts.setup import PATHS
from core.ledger import Ledger
from core.parsers import parse


def _project(root: Path):
    (root / "value.py").write_text("value = 1\n", encoding="utf8")
    command = "python -m pytest"
    save(root, Config(profile="guide", auto_detect=False, commands={"tests": command}))
    ledger = Ledger(root=root, task="feedback-delivery-task")
    ledger.save()
    return ledger, command


def _deliver(root, command, *, host="claude", source="host", respond=None, between=None):
    """One generic result reaching feedback inside a launcher-shaped callback.

    Without ``respond`` the direct transport renders and flushes the context;
    with it, ``respond`` builds the whole rendered response an adapter flushed.
    """
    from core.feedback_delivery import collect, emitted

    generic = parse(command + " | tail -15", "1 passed in 0.01s", 0, root)
    with readiness.ingress(source), collect():
        with readiness.callback(host, root, "PostToolUse", {"session_id": "private-session"}):
            text = feedback(Ledger.load(root), generic, command + " | tail -15")
            assert text
            if between:
                between()
            if respond:
                emitted(respond(text))
            else:
                transport.emit("PostToolUse", {"additionalContext": text})
    return text


def _exact(root, command, output="1 passed in 0.01s", code=0, host="claude"):
    records = parse(command, output, code, root)
    ledger = Ledger.load(root)
    ledger.add(records)
    ledger.save()
    with readiness.ingress("host"):
        with readiness.callback(host, root, "PostToolUse", {"session_id": "private-session"}):
            readiness.record_receipts(records, ledger.task)


@pytest.mark.parametrize("host", sorted(PATHS))
def test_emitted_feedback_and_later_exact_native_receipt_remain_separate_observations(tmp_path, host):
    from core.feedback_delivery import inspect

    ledger, command = _project(tmp_path)
    text = _deliver(tmp_path, command, host=host)
    _exact(tmp_path, command, host=host)

    value = inspect(Ledger.load(tmp_path))

    assert value["state"] == "emitted"
    assert value["intents"] == 1 and value["emitted"] == 1
    assert value["followups"] == [{"declaration": "tests", "state": "current"}]
    assert value["model_consumption"] == "unproven"
    from core.report import end_report
    report = end_report(Ledger.load(tmp_path))
    assert "Feedback delivery (informational; model consumption unproven): emitted; intents 1, native emissions 1" in report
    assert "later exact native receipt tests: current" in report
    stored = (tmp_path / ".elevenpowers" / "ledger.json").read_text(encoding="utf8")
    from core.feedback_delivery import EMITTED, INTENT
    notes = [json.loads(d["why"]) for d in json.loads(stored)["decisions"] if d["what"] in (INTENT, EMITTED)]
    stored_values = [value for note in notes for value in note.values() if isinstance(value, str)]
    assert len(notes) == 2 and all(text not in value for value in stored_values)
    assert "private-session" not in stored


def test_replayed_feedback_records_intent_without_native_emission(tmp_path):
    from core.feedback_delivery import inspect

    _, command = _project(tmp_path)
    _deliver(tmp_path, command, source="replay")

    value = inspect(Ledger.load(tmp_path))

    assert (value["state"], value["intents"], value["emitted"]) == ("intent", 1, 0)
    assert value["followups"] == []


@pytest.mark.parametrize("respond", [
    lambda text: {"systemMessage": text},
    lambda text: {"hookSpecificOutput": {"reason": text}},
    lambda text: {"hookSpecificOutput": {"hookSpecificOutput": {"additionalContext": text}}},
    lambda text: {"additionalContext": text[: len(text) // 2]},
], ids=["unsupported-field", "unsupported-nested-field", "too-deep", "partial-context"])
def test_feedback_outside_a_supported_complete_context_is_not_an_emission(tmp_path, respond):
    from core.feedback_delivery import inspect

    _, command = _project(tmp_path)
    _deliver(tmp_path, command, respond=respond)

    assert inspect(Ledger.load(tmp_path))["state"] == "intent"


@pytest.mark.parametrize("respond", [
    lambda text: {"additionalContext": text},
    lambda text: {"additional_context": "before\n" + text},
    lambda text: {"hookSpecificOutput": {"additionalContext": text}},
], ids=["top-level", "snake-case-combined", "nested"])
def test_rendered_supported_context_field_is_an_emission(tmp_path, respond):
    from core.feedback_delivery import inspect

    _, command = _project(tmp_path)
    _deliver(tmp_path, command, respond=respond)

    assert inspect(Ledger.load(tmp_path))["state"] == "emitted"


@pytest.mark.parametrize("change", ["removed", "reconfigured", "reinstalled"])
def test_activation_changed_before_flush_is_not_an_emission(tmp_path, change):
    from core.feedback_delivery import inspect
    from core.hosts.setup import config_path

    _, command = _project(tmp_path)
    settings = config_path("claude", tmp_path)
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text("{}", encoding="utf8")
    readiness.configured("claude", tmp_path, settings)

    def move():
        if change == "removed":
            readiness.removed("claude", tmp_path)
        elif change == "reconfigured":
            settings.write_text('{"hooks": {}}', encoding="utf8")
        else:
            readiness.configured("claude", tmp_path, settings, changed=True)

    _deliver(tmp_path, command, between=move)

    assert inspect(Ledger.load(tmp_path))["state"] == "intent"


def test_candidates_flushed_by_a_replay_launcher_are_not_an_emission(tmp_path):
    from core.feedback_delivery import inspect

    _, command = _project(tmp_path)

    def replay_flush(text):
        from core.feedback_delivery import emitted
        with readiness.ingress("replay"):
            emitted({"additionalContext": text})
        return {}

    _deliver(tmp_path, command, respond=replay_flush)

    assert inspect(Ledger.load(tmp_path))["state"] == "intent"


@pytest.mark.parametrize("output, code, state", [
    ("1 failed in 0.01s", 1, "failed"),
    ("no tests ran in 0.01s", 5, "incomplete"),
])
def test_later_exact_receipt_reports_its_own_declared_state(tmp_path, output, code, state):
    from core.feedback_delivery import inspect

    _, command = _project(tmp_path)
    _deliver(tmp_path, command)
    _exact(tmp_path, command, output, code)

    assert inspect(Ledger.load(tmp_path))["followups"] == [{"declaration": "tests", "state": state}]


def test_exact_receipt_before_the_emission_is_not_a_followup(tmp_path):
    from core.feedback_delivery import inspect

    _, command = _project(tmp_path)
    _exact(tmp_path, command)
    (tmp_path / "value.py").write_text("value = 2\n", encoding="utf8")
    _deliver(tmp_path, command)

    assert inspect(Ledger.load(tmp_path))["followups"] == [{"declaration": "tests", "state": "unobserved"}]


@pytest.mark.parametrize("why", ["[1]", "\"text\"", "{\"id\": 1}", "not json"])
def test_malformed_delivery_notes_do_not_break_the_completion_report(tmp_path, why):
    from core.feedback_delivery import EMITTED, INTENT
    from core.report import end_report

    _project(tmp_path)
    ledger = Ledger.load(tmp_path)
    ledger.note(INTENT, why)
    ledger.note(EMITTED, why)
    ledger.save()

    assert "Feedback delivery" not in end_report(Ledger.load(tmp_path))


def test_intent_observations_stay_bounded(tmp_path):
    from core.feedback_delivery import INTENT, intent

    _project(tmp_path)
    for index in range(20):
        intent(tmp_path, "feedback-delivery-task", ("tests",), f"advice {index}")

    notes = [d for d in Ledger.load(tmp_path).decisions if d.get("what") == INTENT]
    assert len(notes) == 16


OWNED = Path(__file__).resolve().parents[1] / "plugin/bin/ep_check.py"


def _actual_project(root: Path):
    (root / "value.py").write_text("value = 1\n", encoding="utf8")
    (root / "test_value.py").write_text("from value import value\n\ndef test_value():\n    assert value == 1\n",
                                        encoding="utf8")
    command = f'"{sys.executable}" -m pytest -q -p no:cacheprovider test_value.py'
    save(root, Config(profile="guide", auto_detect=False, commands={"tests": command}, strength={"enabled": False}))
    Ledger(root=root, task="feedback-delivery-task").save()
    return command


def _host(root, command, output, code=0, source="host"):
    from core.feedback_delivery import collect
    from core.hook import dispatch

    payload = {"cwd": str(root), "session_id": "private-session", "tool_name": "Bash",
               "tool_input": {"command": command}, "tool_response": {"stdout": output, "exit_code": code}}
    with readiness.ingress(source), collect():
        assert dispatch("PostToolUse", payload) == 0


def _run(command, root):
    done = subprocess.run(command, cwd=root, shell=True, capture_output=True, text=True, timeout=120,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    return done.stdout + done.stderr, done.returncode


def _generic(root, command, capsys):
    output, code = _run(command, root)
    _host(root, command + " 2>&1 | tail -15", output, code)
    assert "Owned check arguments:" in capsys.readouterr().out


def _owned(root, *extra):
    command = f'"{sys.executable}" "{OWNED}" tests --project "{root}"' + "".join(" " + arg for arg in extra)
    output, code = _run(command, root)
    return command, output, code


@pytest.mark.parametrize("extra", [(), ("--json",)], ids=["text", "json"])
def test_owned_run_after_emitted_feedback_is_a_later_exact_native_receipt(tmp_path, capsys, extra):
    from core.feedback_delivery import inspect

    command = _actual_project(tmp_path)
    _generic(tmp_path, command, capsys)
    owned, output, code = _owned(tmp_path, *extra)
    assert code == 0
    _host(tmp_path, owned, output)

    assert inspect(Ledger.load(tmp_path))["followups"] == [{"declaration": "tests", "state": "current"}]


def test_owned_output_from_before_the_emission_is_not_a_followup(tmp_path, capsys):
    from core.feedback_delivery import inspect

    command = _actual_project(tmp_path)
    owned, earlier, code = _owned(tmp_path)
    assert code == 0
    (tmp_path / "value.py").write_text("value = 1  # moved\n", encoding="utf8")
    _generic(tmp_path, command, capsys)
    _host(tmp_path, owned, earlier)

    assert inspect(Ledger.load(tmp_path))["followups"] == [{"declaration": "tests", "state": "unobserved"}]


@pytest.mark.parametrize("source", ["host", "replay"])
def test_owned_envelope_without_its_own_receipt_links_nothing(tmp_path, capsys, source):
    from core.feedback_delivery import inspect

    command = _actual_project(tmp_path)
    _generic(tmp_path, command, capsys)
    owned, output, code = _owned(tmp_path)
    if source == "host":
        output = "".join(f"Attempt: {'0' * 64}\n" if line.startswith("Attempt:") else line
                         for line in output.splitlines(keepends=True))
    _host(tmp_path, owned, output, source=source)

    assert inspect(Ledger.load(tmp_path))["followups"] == [{"declaration": "tests", "state": "unobserved"}]
