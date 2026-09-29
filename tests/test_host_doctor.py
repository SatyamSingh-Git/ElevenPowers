import json
from pathlib import Path
import subprocess
import sys


def test_codex_doctor_reports_missing_then_configured_without_claiming_live(tmp_path):
    from core.hosts.doctor import report
    from core.hosts.setup import install
    text, ok = report("codex", tmp_path)
    assert not ok and "missing" in text
    install("codex", tmp_path, sys.executable, Path(__file__).resolve().parents[1])
    text, ok = report("codex", tmp_path)
    assert ok and "configuration" in text
    assert "Live host session: not verified" in text


def test_codex_launcher_records_pass_fail_and_incomplete(tmp_path):
    from core.config import Config, save
    from core.ledger import Ledger
    save(tmp_path, Config(profile="off", commands={"tests": "npm run ci"}))
    launcher = Path(__file__).resolve().parents[1] / "plugin/bin/ep_host.py"
    states = []
    for raw in [{"exit_code": 0}, {"exit_code": 1}, {"stdout": "unknown"}]:
        payload = {"cwd": str(tmp_path), "tool_name": "Bash", "tool_input": {"command": "npm run ci"}, "tool_response": raw}
        done = subprocess.run([sys.executable, str(launcher), "codex", "PostToolUse"],
                              input=json.dumps(payload), text=True, capture_output=True, timeout=20)
        assert done.returncode == 0, done.stderr
        json.loads(done.stdout)
        record = Ledger.load(tmp_path).evidence[-1]
        states.append((record.result.value, record.execution))
    assert states == [("pass", "complete"), ("fail", "complete"), ("error", "incomplete")]


def test_gemini_doctor_explains_permission_and_evidence_limits(tmp_path):
    from core.hosts.setup import install
    from core.hosts.doctor import report
    install("gemini", tmp_path, sys.executable, Path(__file__).resolve().parents[1])
    text, ok = report("gemini", tmp_path)
    assert ok
    assert "approval requests unavailable" in text
    assert "prose-only" in text
    assert "Live host session: not verified" in text


def test_gemini_launcher_receipt_states(tmp_path):
    from core.config import Config, save
    from core.ledger import Ledger
    save(tmp_path, Config(profile="off", commands={"tests": "npm run ci"}))
    launcher = Path(__file__).resolve().parents[1] / "plugin/bin/ep_host.py"
    for raw, expected in [({"data": {"exitCode": 0}}, "pass"), ({"data": {"exitCode": 1}}, "fail"), ({"llmContent": "ok"}, "error")]:
        payload = {"cwd": str(tmp_path), "tool_name": "run_shell_command", "tool_input": {"command": "npm run ci"}, "tool_response": raw}
        result = subprocess.run([sys.executable, str(launcher), "gemini", "AfterTool"], input=json.dumps(payload), text=True, capture_output=True, timeout=20)
        assert result.returncode == 0, result.stderr
        assert Ledger.load(tmp_path).evidence[-1].result.value == expected
