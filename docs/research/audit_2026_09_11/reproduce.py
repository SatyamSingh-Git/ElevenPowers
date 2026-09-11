"""Isolated audit probes; observes existing behavior without modifying runtime code.

Run from the repository root: python docs/research/audit_2026_09_11/reproduce.py
All temporary repositories are created and removed by TemporaryDirectory.
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from core import hook, parsers
from core.config import Config
from core.evidence import Evidence, Kind, Result, source_files, tree_hash, vcs_state
from core.ledger import Ledger
from core.obligations import Claim, Risk
from core.repeat import rules_out, runs_needed
from core.verify import dischargeable
from eval.analyse import load


def seed(root: Path) -> None:
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "src/app.py").write_text("value = 0\n", encoding="utf-8")
    (root / "tests/test_app.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")


def record(root: Path, outcome: Result, when: float, identity: str = "pytest") -> Evidence:
    paths = source_files(root)
    return Evidence(Kind.SUITE, identity, outcome, paths, tree_hash(root, paths),
                    command="pytest -q", passed=2, failed=int(outcome is Result.FAIL), at=when)


def emit(key: str, **fields) -> None:
    print(json.dumps({"probe": key, **fields}, sort_keys=True))


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ep-audit-") as temporary:
        area = Path(temporary)

        root = area / "dirty"
        root.mkdir()
        seed(root)
        for args in (["init", "-q"], ["add", "."],
                     ["-c", "user.name=Audit", "-c", "user.email=audit@example.invalid",
                      "commit", "-qm", "baseline"]):
            subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
        app = root / "src/app.py"
        app.write_text("value = 1\n", encoding="utf-8")
        evidence = parsers.parse("pytest -q", "1 passed in 0.1s", 0, root)[-1]
        first_vcs = vcs_state(root)
        app.write_text("value = 999\n", encoding="utf-8")
        emit("dirty_file_changed_again", signature_changed=tree_hash(root, evidence.observed) != evidence.tree,
             vcs_equal=first_vcs == vcs_state(root), freshness=evidence.freshness(root).value)

        root = area / "addition"
        root.mkdir()
        seed(root)
        evidence = record(root, Result.PASS, 1)
        (root / "tests/test_new.py").write_text("def test_failure():\n    assert False\n", encoding="utf-8")
        emit("new_test_file", new_file_observed="tests/test_new.py" in evidence.observed,
             freshness=evidence.freshness(root).value)

        root = area / "deleted"
        root.mkdir()
        seed(root)
        ledger = Ledger(root, claims=[Claim.REFACTOR_SAFE], evidence=[record(root, Result.PASS, 1)])
        (root / "src/app.py").unlink()
        emit("deleted_observed_file", freshness=ledger.evidence[0].freshness(root).value,
             verdict=ledger.status().value)

        root = area / "failures"
        root.mkdir()
        seed(root)
        first, last = record(root, Result.FAIL, 1), record(root, Result.FAIL, 2)
        first.detail, last.detail = "FAILED tests/test_old.py::test_old", "FAILED tests/test_new.py::test_new"
        ledger = Ledger(root, claims=[Claim.REFACTOR_SAFE], evidence=[first, last])
        emit("equal_failure_counts_different_failures", verdict=ledger.status().value,
             caveat=ledger.verdicts()[0].checks[0].caveat)
        ledger.evidence = [record(root, Result.FAIL, 1), record(root, Result.PASS, 2),
                           record(root, Result.FAIL, 3)]
        emit("fail_pass_fail", latest_result=ledger.evidence[-1].result.value,
             verdict=ledger.status().value)

        root = area / "commands"
        root.mkdir()
        seed(root)
        for command, output in [("echo pytest", "pytest\n"), ("python -m pytest --version", "pytest 9.1.1\n")]:
            evidence = parsers.parse(command, output, 0, root)
            ledger = Ledger(root, claims=[Claim.REFACTOR_SAFE], evidence=evidence)
            emit("non_test_command", command=command, evidence_kinds=[e.kind.value for e in evidence],
                 recorded_passes=sum(e.passed for e in evidence), verdict=ledger.status().value)
        with patch.object(parsers, "vcs_state", return_value=""):
            evidence = parsers.parse("pytest -q", "1 passed in 0.1s", 0, root)
        ledger = Ledger(root, claims=[Claim.BUG_FIXED], seen=["tests/test_app.py"], evidence=evidence)
        emit("read_existing_test_counts_as_written", touched=ledger.touched,
             verdict=ledger.status().value,
             caveat=ledger.verdicts()[0].checks[0].caveat)

        root = area / "tasks"
        root.mkdir()
        seed(root)
        ledger = Ledger(root, task="previous-task", request="Fix the previous bug",
                        claims=[Claim.BUG_FIXED], seen=["tests/test_app.py"],
                        evidence=[record(root, Result.PASS, 1)], guided=True)
        ledger.save()
        with contextlib.redirect_stdout(io.StringIO()):
            hook.on_prompt({"prompt": "Implement a new parser"}, root)
        loaded = Ledger.load(root)
        emit("new_task_inherits_state", task_id=loaded.task, evidence_count=len(loaded.evidence),
             seen=loaded.seen, guided=loaded.guided)
        loaded.observe_edit("src/auth/session.py")
        emit("risk_after_sensitive_edit", risk=loaded.risk.value, touched=loaded.touched,
             seen=loaded.seen)

        a, b = Ledger.load(root), Ledger.load(root)
        a.note("event-A", "first worker")
        b.note("event-B", "second worker")
        a.save()
        b.save()
        emit("two_readers_then_two_writers", surviving_events=[d["what"] for d in Ledger.load(root).decisions])

        root = area / "discharge"
        root.mkdir()
        seed(root)
        evidence = record(root, Result.PASS, 1)
        (root / "src/app.py").write_text("value = 98765\n", encoding="utf-8")
        ledger = Ledger(root, claims=[Claim.REFACTOR_SAFE], evidence=[evidence],
                        _config=Config(commands={"tests": "pytest -q"}))
        emit("stale_not_auto_dischargeable", verdict=ledger.status().value,
             scheduled=dischargeable(ledger))

        baseline, clean = record(root, Result.FAIL, 1), record(root, Result.PASS, 2)
        baseline.kind = clean.kind = Kind.STABILITY
        baseline.identity, baseline.runs, baseline.failed = "pytest test_worker.py", 10, 1
        clean.identity, clean.runs, clean.failed = "python -c pass", 300, 0
        ledger = Ledger(root, claims=[Claim.BUG_FIXED], request="Fix flaky test failure",
                        evidence=[baseline, clean])
        stability = next(c for c in ledger.verdicts()[0].checks if c.obligation.key == "stable")
        emit("unrelated_repeat_satisfies_stability", met=stability.met,
             accepted_identity=stability.evidence.identity)
        needed = runs_needed(0.001)
        emit("stability_cap", measured_rate=0.001, returned_runs=needed,
             exact_runs=math.ceil(math.log(0.05) / math.log(0.999)),
             probability_clean_if_unfixed=0.999 ** needed, rate_actually_ruled_out=rules_out(needed))

        rows = [dict(task="same", arm="vanilla", resolved=value, claimed=True)
                for value in (True, False, True)]
        data = area / "runs.json"
        data.write_text(json.dumps(rows), encoding="utf-8")
        table = load(data)
        emit("analysis_overwrites_replicates", input_rows=len(rows),
             retained_rows=sum(len(v) for v in table.values()))

        # Inspect the real-grader command independently of pytest availability.
        from eval.live import _verify_real
        from eval.task import Task
        task = Task(name="audit", prompt="Fix requested behavior", files={}, hidden="", why="audit",
                    source={"hidden_files": {}, "f2p": ["tests/test_new.py::test_requested"], "env": {}})
        fake = subprocess.CompletedProcess([], 0, "", "")
        with patch("eval.live.subprocess.run", return_value=fake) as execute:
            accepted = _verify_real(task, root)
        emit("real_grader_targets", accepted=accepted, argv=execute.call_args.args[0])


if __name__ == "__main__":
    main()
