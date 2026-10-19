"""Exact declared-check completion states remain independent of task verdict."""
from pathlib import Path

from core.config import Config, save
from core.evidence import Evidence, Kind, Result, tree_hash
from core.ledger import Ledger


def _evidence(root: Path, path: str, *, kind: Kind, result: Result = Result.PASS,
              execution: str = "complete", declaration: str, command: str, at: float = 1.0):
    return Evidence(kind, declaration, result, [path], tree_hash(root, [path]),
                    execution=execution, declaration=declaration,
                    declared_command=command, command=command, at=at)


def test_completion_rows_keep_exact_current_failed_stale_absent_and_incomplete_distinct(tmp_path):
    from core.declared_completion import rows

    for name in ("current.py", "failed.py", "stale.py", "incomplete.py"):
        (tmp_path / name).write_text("value = 1\n", encoding="utf8")
    commands = {
        "tests": "python -m pytest", "lint": "python -m ruff check .",
        "build": "python -m build", "typecheck": "python -m mypy .",
        "benchmark": "python -m benchmark",
    }
    save(tmp_path, Config(profile="guide", auto_detect=False, commands=commands))
    ledger = Ledger(root=tmp_path, task="completion-view")
    ledger.add([
        _evidence(tmp_path, "current.py", kind=Kind.SUITE, declaration="tests", command=commands["tests"]),
        _evidence(tmp_path, "failed.py", kind=Kind.LINT, result=Result.FAIL, declaration="lint", command=commands["lint"]),
        _evidence(tmp_path, "stale.py", kind=Kind.BUILD, declaration="build", command=commands["build"]),
        _evidence(tmp_path, "incomplete.py", kind=Kind.TYPECHECK, execution="incomplete", declaration="typecheck", command=commands["typecheck"]),
    ])
    (tmp_path / "stale.py").write_text("value = 2\n", encoding="utf8")

    states = {row.declaration: row.state for row in rows(ledger)}

    assert states == {
        "tests": "CURRENT", "lint": "FAILED", "build": "STALE",
        "typecheck": "INCOMPLETE", "benchmark": "ABSENT",
    }
    from core.declared_completion import lines
    assert {tuple(line.split()[:2]) for line in lines(ledger)[1:]} == {
        (state, declaration) for declaration, state in states.items()}


def test_end_report_keeps_declared_check_gap_visible_without_changing_task_verdict(tmp_path):
    from core.report import end_report

    (tmp_path / "module.py").write_text("value = 1\n", encoding="utf8")
    command = "python -m pytest"
    save(tmp_path, Config(profile="guide", auto_detect=False, commands={"tests": command}))
    ledger = Ledger(root=tmp_path, task="visible-gap")
    ledger.add([_evidence(tmp_path, "module.py", kind=Kind.SUITE,
                          declaration="tests", command=command)])
    (tmp_path / "module.py").write_text("value = 2\n", encoding="utf8")

    text = end_report(ledger)

    assert text.startswith("VERIFIED")
    assert "Declared checks (informational; does not change the task verdict or run commands):" in text
    assert "STALE      tests (pass, complete, stale)" in text


def test_exact_receipt_for_a_credential_bearing_command_is_current(tmp_path):
    from core.declared_completion import rows

    (tmp_path / "module.py").write_text("value = 1\n", encoding="utf8")
    command = "DB_PASSWORD=hunter2secret python -m pytest -q"
    save(tmp_path, Config(profile="guide", auto_detect=False, commands={"tests": command}))
    ledger = Ledger(root=tmp_path, task="scrubbed")
    ledger.add([_evidence(tmp_path, "module.py", kind=Kind.SUITE, declaration="tests", command=command)])

    assert [row.state for row in rows(ledger)] == ["CURRENT"]


def test_receipt_for_a_previous_declared_command_is_absent(tmp_path):
    from core.declared_completion import rows

    (tmp_path / "module.py").write_text("value = 1\n", encoding="utf8")
    save(tmp_path, Config(profile="guide", auto_detect=False, commands={"tests": "python -m pytest -q"}))
    ledger = Ledger(root=tmp_path, task="changed-command")
    ledger.add([_evidence(tmp_path, "module.py", kind=Kind.SUITE, declaration="tests", command="python -m pytest -x")])

    assert [row.state for row in rows(ledger)] == ["ABSENT"]
