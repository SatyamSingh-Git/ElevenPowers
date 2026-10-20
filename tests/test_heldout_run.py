"""The sealed held-out runner, with only the external model process substituted."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from eval import heldout_run as h
from tests.test_heldout_grading import _task


def _corpus(tmp_path, names=("t",)):
    tasks = []
    for name in names:
        task, gold = _task(tmp_path / name)
        tasks.append({**task.source, "name": name, "prompt": "Make value() return 2.", "import_names": ["pkg"],
                      "url": "https://example.invalid/" + name, "gold": gold})
    environments = {t["url"]: {"state": "ready", "test_dir": "test/"} for t in tasks}
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps({"tasks": tasks, "environments": environments}), encoding="utf8")
    return path, tasks


def _host(tasks, calls, *, tools=(), model="claude-sonnet-5-5"):
    actual = h.run

    def external(command, **kwargs):
        if not (isinstance(command, list) and command[0] == "fake-host"):
            return actual(command, **kwargs)
        if command[-1] == "--version":
            return SimpleNamespace(returncode=0, stdout="fake test host", stderr="")
        root = Path(kwargs["cwd"])
        settings = root / ".claude" / "settings.local.json"
        calls.append({"hooks": bool(settings.exists() and json.loads(settings.read_text(encoding="utf8")).get("hooks")),
                      "config": (root / ".elevenpowers" / "config.json").exists(),
                      "history": (root / ".git").exists() and h.run(["git", "rev-list", "--count", "HEAD"], cwd=root,
                                                                    timeout=10, shell=False).stdout.strip(),
                      "env": kwargs["env"]})
        (root / "pkg" / "mod.py").write_text("def value():\n    return 2\n", encoding="utf8")
        events = [{"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": c}} for c in tools]}},
            {"type": "result", "is_error": False, "total_cost_usd": 0.5, "modelUsage": {model: {}}}]
        return SimpleNamespace(returncode=0, stdout="\n".join(json.dumps(e) for e in events), stderr="")
    return external


def _prepared(tmp_path, monkeypatch, **kwargs):
    corpus, tasks = _corpus(tmp_path, **kwargs)
    protocol = h.prepare(tmp_path / "batch", corpus, replicates=1, seconds=60)
    monkeypatch.setattr(h.subscription, "auth", lambda *a: True)
    return protocol, tasks


def test_arms_interleave_per_task_and_first_arm_alternates(tmp_path):
    corpus, _ = _corpus(tmp_path, names=("a", "b"))
    protocol = h.prepare(tmp_path / "batch", corpus, replicates=2, seconds=60)
    assert protocol["slots"] == ["a--ordinary--0", "a--assisted--0", "b--assisted--0", "b--ordinary--0",
                                 "a--assisted--1", "a--ordinary--1", "b--ordinary--1", "b--assisted--1"]


def test_the_seal_refuses_a_changed_corpus_or_runtime(tmp_path, monkeypatch):
    protocol, _ = _prepared(tmp_path, monkeypatch)
    slot = protocol["slots"][0]
    h.verify(tmp_path / "batch", slot)
    frozen = tmp_path / "batch" / "corpus.json"
    original = frozen.read_bytes()
    frozen.write_bytes(original.replace(b"Make value()", b"Make  value()"))
    with pytest.raises(ValueError, match="corpus"):
        h.verify(tmp_path / "batch", slot)
    frozen.write_bytes(original)
    monkeypatch.setattr(h, "fingerprint", lambda: "0" * 64)
    with pytest.raises(ValueError, match="runtime"):
        h.verify(tmp_path / "batch", slot)


def test_a_launched_slot_is_graded_once_and_never_relaunched(tmp_path, monkeypatch):
    protocol, tasks = _prepared(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(h, "run", _host(tasks, calls))
    slot = protocol["slots"][0]
    result = h.execute(tmp_path / "batch", slot, "fake-host")
    assert (result["state"], result["resolved"], result["task"], result["arm"]) == ("graded", True, "t", "ordinary")
    assert result["vacuous"] is True and result["cost"] == 0.5
    assert calls[0]["history"] == "1"
    assert "pkg/mod.py" in (tmp_path / "batch" / slot / "patch.diff").read_text(encoding="utf8")
    assert ".venv" not in (tmp_path / "batch" / slot / "patch.diff").read_text(encoding="utf8")
    assert calls[0]["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == "claude-sonnet-5-5"
    with pytest.raises(ValueError, match="retry"):
        h.execute(tmp_path / "batch", slot, "fake-host")
    assert len(calls) == 1


def test_assisted_is_installed_with_the_declared_suite_and_ordinary_has_nothing(tmp_path, monkeypatch):
    protocol, tasks = _prepared(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(h, "run", _host(tasks, calls))
    for slot in protocol["slots"]:
        h.execute(tmp_path / "batch", slot, "fake-host")
    ordinary, assisted = calls
    assert (ordinary["hooks"], ordinary["config"]) == (False, False)
    assert (assisted["hooks"], assisted["config"]) == (True, True)
    work = tmp_path / "batch" / "t--assisted--0" / "work"
    declared = json.loads((work / ".elevenpowers" / "config.json").read_text(encoding="utf8"))
    assert declared["commands"]["tests"] == "python -m pytest test -q"


def test_the_canary_is_rechecked_before_launch(tmp_path, monkeypatch):
    protocol, tasks = _prepared(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(h, "run", _host(tasks, calls))
    monkeypatch.setattr(h, "canary", lambda *a: False)
    result = h.execute(tmp_path / "batch", protocol["slots"][0], "fake-host")
    assert result["state"] == "canary_failed" and calls == []


def test_a_network_reach_is_recorded_and_not_credited(tmp_path, monkeypatch):
    protocol, tasks = _prepared(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(h, "run", _host(tasks, calls, tools=["git log --oneline", "curl -s https://pypi.org/x"]))
    result = h.execute(tmp_path / "batch", protocol["slots"][0], "fake-host")
    assert result["state"] == "closed_book_breach" and result["resolved"] is True
    assert result["breaches"] == ["curl -s https://pypi.org/x"]
    assert result["history_reads"] == ["git log --oneline"]


def test_history_reads_alone_do_not_withhold_credit(tmp_path, monkeypatch):
    protocol, tasks = _prepared(tmp_path, monkeypatch)
    monkeypatch.setattr(h, "run", _host(tasks, [], tools=["git log --oneline"]))
    result = h.execute(tmp_path / "batch", protocol["slots"][0], "fake-host")
    assert result["state"] == "graded" and result["history_reads"] == ["git log --oneline"]


def test_another_model_is_not_graded(tmp_path, monkeypatch):
    protocol, tasks = _prepared(tmp_path, monkeypatch)
    monkeypatch.setattr(h, "run", _host(tasks, [], model="claude-haiku-5-5"))
    result = h.execute(tmp_path / "batch", protocol["slots"][0], "fake-host")
    assert result["state"] == "model_unqualified"


def test_the_workspace_interpreter_does_not_see_the_base_site(tmp_path, monkeypatch):
    import subprocess
    import sys
    from eval.heldout_env import _python
    closed = tmp_path / "closed"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(closed)], check=True, timeout=180)
    corpus, tasks = _corpus(tmp_path)
    # pytest stands in for the task's package: installed for the base interpreter, absent from the task's venv.
    value = json.loads(corpus.read_text(encoding="utf8"))
    value["tasks"][0].update(python=_python(closed), import_names=["pytest"])
    corpus.write_text(json.dumps(value), encoding="utf8")
    protocol = h.prepare(tmp_path / "batch", corpus, replicates=1, seconds=60)
    monkeypatch.setattr(h.subscription, "auth", lambda *a: True)
    calls = []
    monkeypatch.setattr(h, "run", _host(tasks, calls))
    result = h.execute(tmp_path / "batch", protocol["slots"][0], "fake-host")
    assert result["state"] != "canary_failed" and len(calls) == 1


def test_collect_reports_every_scheduled_slot_including_unlaunched_ones(tmp_path, monkeypatch):
    from eval.heldout_analyse import analyse
    protocol, tasks = _prepared(tmp_path, monkeypatch)
    monkeypatch.setattr(h, "run", _host(tasks, []))
    h.execute(tmp_path / "batch", protocol["slots"][0], "fake-host")
    records = h.collect(tmp_path / "batch")
    assert [(r["slot"], r["state"]) for r in records] == [("t--ordinary--0", "graded"), ("t--assisted--0", "not_launched")]
    assert analyse(records)["runs"] == {"scheduled": 2, "graded": 1, "incomplete": 1}
