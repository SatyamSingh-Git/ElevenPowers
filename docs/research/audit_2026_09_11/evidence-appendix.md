# Audit evidence appendix

This appendix records checks of the existing implementation at commit `9a21de12cc1de43e22896dbcc353d6927624643f`, performed on 11 September 2026. It is evidence for [findings.md](findings.md), not an implementation change.

## Scope and environment

- Workspace: `E:/ElevenPowers`; Windows; Python 3.13.2.
- Existing runtime, evaluator, tests and plans were not edited.
- The newly created `reproduce.py` is retained under the user's explicit exception for work already done. It creates and removes isolated temporary repositories and does not patch project implementation files. Two additional probes below were executed through standard input; they created no additional project scripts.
- Pytest 9.1.1 and its dependencies were installed into a task-specific temporary directory, not into the project or the global Python environment. Access to that temporary installation required an approved elevated execution. No agent inference runs were purchased or launched.
- The historical mined corpus, candidate patches and run-level result artifacts were not available in this checkout. Historical performance claims were inspected in project documentation, not independently rerun.

## Existing test suite

Executed with the temporary pytest directory on `PYTHONPATH` and third-party pytest plugin autoload disabled:

```powershell
$auditDeps = Join-Path $env:TEMP 'elevenpowers-audit-deps'
$env:PYTHONPATH = $auditDeps
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -m pytest tests -q
```

Observed result: **379 passed in 108.32 seconds**, process exit code 0. This validates the existing tests on this environment; it does not invalidate the counterexamples below. No implementation fixes were made.

## Sixteen isolated observations

Run from the repository root:

```powershell
python docs/research/audit_2026_09_11/reproduce.py
```

The script invokes the existing parsers and ledger on small fixtures. Most command outputs are supplied as parser inputs; they are not claims that a real test command was run in those probes. The final `real_grader_targets` observation mocks the subprocess to inspect its arguments. A separate end-to-end subprocess check follows below.

These are sixteen observations, not sixteen statistically independent findings or a representative defect rate. Several exercise the same underlying design defect. The lost-update probe deterministically reproduces two readers followed by two writers; it does not estimate race frequency in live sessions.

```jsonl
{"freshness": "fresh", "probe": "dirty_file_changed_again", "signature_changed": true, "vcs_equal": true}
{"freshness": "fresh", "new_file_observed": false, "probe": "new_test_file"}
{"freshness": "gone", "probe": "deleted_observed_file", "verdict": "VERIFIED"}
{"caveat": "no new failures", "probe": "equal_failure_counts_different_failures", "verdict": "VERIFIED"}
{"latest_result": "fail", "probe": "fail_pass_fail", "verdict": "VERIFIED"}
{"command": "echo pytest", "evidence_kinds": ["test_suite"], "probe": "non_test_command", "recorded_passes": 0, "verdict": "VERIFIED"}
{"command": "python -m pytest --version", "evidence_kinds": ["test_suite"], "probe": "non_test_command", "recorded_passes": 0, "verdict": "VERIFIED"}
{"caveat": "a test was written and the suite that runs it passed", "probe": "read_existing_test_counts_as_written", "touched": [], "verdict": "VERIFIED"}
{"evidence_count": 1, "guided": true, "probe": "new_task_inherits_state", "seen": ["tests/test_app.py"], "task_id": "previous-task"}
{"probe": "risk_after_sensitive_edit", "risk": "low", "seen": ["tests/test_app.py", "src/auth/session.py"], "touched": []}
{"probe": "two_readers_then_two_writers", "surviving_events": ["event-B"]}
{"probe": "stale_not_auto_dischargeable", "scheduled": [], "verdict": "STALE"}
{"accepted_identity": "python -c pass", "met": true, "probe": "unrelated_repeat_satisfies_stability"}
{"exact_runs": 2995, "measured_rate": 0.001, "probability_clean_if_unfixed": 0.7407070321560992, "probe": "stability_cap", "rate_actually_ruled_out": 0.00993608194445772, "returned_runs": 300}
{"input_rows": 3, "probe": "analysis_overwrites_replicates", "retained_rows": 1}
{"accepted": true, "argv": ["C:\\Python313\\python.exe", "-m", "pytest", "tests/test_new.py::test_requested", "-q", "--no-header"], "probe": "real_grader_targets"}
```

## Current documented failure-hook shape

The current [Claude Code hooks reference](https://code.claude.com/docs/en/hooks#posttoolusefailure-input) documents failure information at the top level of the event. This minimal fixture follows that shape:

```python
import contextlib, io, json, tempfile
from pathlib import Path
from core.payload import read_result
from core import hook
from core.ledger import Ledger

with tempfile.TemporaryDirectory(prefix='ep-hook-audit-') as temp:
    root = Path(temp)
    payload = {
        'hook_event_name': 'PostToolUseFailure',
        'tool_name': 'Bash',
        'tool_input': {'command': 'python -m pytest -q'},
        'error': 'Exit code 1\n1 failed in 0.1s',
        'is_interrupt': False,
    }
    result = read_result(payload)
    with contextlib.redirect_stdout(io.StringIO()):
        code = hook.on_post_tool(payload, root)
    print(json.dumps({
        'probe': 'documented_failure_hook_shape',
        'readable': result.readable,
        'exit_code': result.exit_code,
        'captured_evidence': len(Ledger.load(root).evidence),
        'handler_exit': code,
    }))
```

Observed:

```json
{"probe": "documented_failure_hook_shape", "readable": false, "exit_code": 1, "captured_evidence": 0, "handler_exit": 0}
```

This proves a mismatch against the documented shape. It does **not** establish which payload schema every historical Claude Code version emitted. A raw hook capture from the pinned supported host remains necessary. The hook records a blind spot, but it adds no failing evidence in this case.

## Grader accepts a patch with an existing-test regression

This check used actual pytest subprocesses from the temporary installation:

```python
import json, subprocess, sys, tempfile
from pathlib import Path
from eval.live import _verify_real
from eval.task import Task

with tempfile.TemporaryDirectory(prefix='ep-grader-audit-') as temp:
    root = Path(temp)
    (root / 'tests').mkdir()
    (root / 'conftest.py').write_text('', encoding='utf-8')
    (root / 'app.py').write_text(
        'def requested(): return 1\ndef existing(): return 999\n',
        encoding='utf-8',
    )
    (root / 'tests/test_existing.py').write_text(
        'from app import existing\ndef test_existing(): assert existing() == 0\n',
        encoding='utf-8',
    )
    hidden = 'from app import requested\ndef test_requested(): assert requested() == 1\n'
    task = Task('audit', 'Correct requested()', '', '', '', source={
        'hidden_files': {'tests/test_new.py': hidden},
        'f2p': ['tests/test_new.py::test_requested'],
        'env': {},
    })
    accepted = _verify_real(task, root)
    regression = subprocess.run(
        [sys.executable, '-m', 'pytest', 'tests/test_existing.py', '-q'],
        cwd=root, capture_output=True, text=True,
    )
    print(json.dumps({
        'probe': 'f2p_pass_existing_regression',
        'grader_accepted': accepted,
        'existing_test_exit': regression.returncode,
        'existing_test_failed': '1 failed' in regression.stdout,
    }))
```

Observed:

```json
{"probe": "f2p_pass_existing_regression", "grader_accepted": true, "existing_test_exit": 1, "existing_test_failed": true}
```

The unused `Task.files` field in this exact probe was supplied as an empty string; the real-task grader accesses only `source`. This fixture demonstrates an acceptance condition, not the prevalence of regressions among the historical twelve candidates.

## Retained reproduction script

The exact source of the already-created, exempted script is included for review:

```python
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
```
