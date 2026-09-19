# Audit evidence — 19 September 2026

Revision inspected: `4e9b797fc0d53561bd326b27611f2ef2dfd2f45f`.

This audit changes no existing source, tests, plans or configuration. Probes create temporary repositories and remove them after execution. They do not run a coding agent or spend model API credits. The fake credential used below is synthetic.

## Existing test coverage checked

The default Python 3.13 interpreter and the bundled runtime had no pytest installed. The registered Windows Store Python 3.11 could not launch under the current permissions. Pytest 9.1.1 and its dependencies were installed into an isolated temporary virtual environment, not into shared packages.

The first test invocation encountered pytest temporary-directory permission errors: 73 passed, 104 setup errors. Re-running with an explicit writable temporary directory completed successfully:

```text
177 passed in 55.08s
```

Command (with the temporary venv's Scripts directory first on PATH and PYTHONDONTWRITEBYTECODE=1):

```powershell
& $auditPython -B -m pytest -p no:cacheprovider --basetemp=E:/ElevenPowers/.audit-20260919-checks tests/test_stress.py tests/test_ratchet.py tests/test_assumptions.py tests/test_tap.py tests/test_radius.py tests/test_atlas.py tests/test_redact.py tests/test_hook.py -q --tb=short --maxfail=3
```

This is a focused suite, not the full repository suite. Optional tree-sitter grammar integration and live host delivery were not exercised. No current paid run was regraded. Process-containment improvements were inspected, not stress-tested on the host.

## Additional probe results

These are observations of the current implementation, not tests asserting the desired behavior. Some cases exercise real git and pytest; some isolate a hook boundary with a mocked ledger load/save. The `off_profile_replays_commands` probe stubs the old-tree command executor and counts calls, so it proves dispatch under the off profile, not the downstream process behavior. The reproduction-kind and pooled-statistic cases use explicit synthetic inputs.

```jsonl
{"probe": "confirm_fail_fast", "records": [["tests/test_b.py::test_b", "pass"]], "reproduction": "tests/test_b.py::test_b", "second_test_executed": false}
{"probe": "confirm_skip", "records": [["tests/test_a.py::test_a", "pass"]], "reproduction": "tests/test_a.py::test_a"}
{"cached": {"tests": "no"}, "fresh_control_passes": false, "initial": {"tests": "no"}, "probe": "stress_cache_after_test_edit"}
{"evidence_count": 0, "probe": "question_creates_proven_snapshot", "snapshot": true, "status_before": "UNVERIFIED", "stop_return": 0}
{"captured_outputs": 0, "probe": "ordinary_producer_output_dropped"}
{"probe": "vacuous_from_absence", "reported": ["tests/test_b.py"]}
{"probe": "reading_tap_file", "records": [["test_suite", "pass", true]]}
{"changed_lines": [1], "git_diff": "", "probe": "unchanged_file_marked_changed"}
{"command_calls": 1, "probe": "off_profile_replays_commands"}
{"caveat": "suite-level: the declared check failed on the base tree and passes now. No individual test was seen red there and green here, so this is the same run that decided discrimination, not a second finding", "probe": "different_check_kinds_form_reproduction", "reproduction": true}
{"after_read": false, "before_read": true, "probe": "read_then_edit_suppresses_brief"}
{"extra_test_survives": true, "probe": "restore_leaves_new_test", "still_differs": true}
{"probe": "evidence_bypasses_output_redaction", "token_in_evidence": true, "token_in_outputs": false}
{"measured": {"arm": "vanilla", "attempts": 1, "coverage": 0.0, "dropped_setup": 0, "gap": 0.0, "last": 0.0, "mixed": 0, "random_pick": 0.0, "replicated": 0, "sweep": "ALL POOLED", "tasks": 1}, "probe": "pooled_overwrites_sweeps"}
```

The fail-fast reproduction deliberately selects three tests. The first fails under `-x`; the second is credited as PASS despite its execution marker never being created. The suite record happens to take the final selected node's identity, so the third node is excluded as a failure. This extra identity collision is why a two-node version did not expose the false positive.

The skip case is independent: pytest marks the only requested node skipped; the runtime emits PASS and accepts it as a named reproduction.

The cache control changes both the source and carried test. A fresh old-tree execution fails, while the cached verdict remains `no` (non-discriminating).

## Reproduce the probes

Run from `E:/ElevenPowers` using Python with pytest installed. The script writes fixture files only under a uniquely named temporary directory in the current directory. Git identity is set only inside that temporary repository. The git restore operation affects only that fixture. The script prints facts; it intentionally does not turn observed bugs into passing assertions about correctness.

```python
import contextlib, io, json, os, subprocess, sys, tempfile
from pathlib import Path
from unittest.mock import patch
from core import hook, ratchet, stress, assumptions, parsers, radius
from core.config import Config
from core.evidence import Evidence, Kind, Result, source_files, tree_hash
from core.ledger import Ledger
from core.obligations import Claim
from eval.pool import pools, measure

def emit(name, **values):
    print(json.dumps({"probe": name, **values}, sort_keys=True))
def git(root, *args):
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()
def setup(root):
    git(root, "init", "-q")
    git(root, "config", "user.email", "audit@example.invalid")
    git(root, "config", "user.name", "Audit")
    (root / "app.py").write_text("value = 1\n")
    (root / "tests").mkdir()
    (root / "tests/test_a.py").write_text("def test_a():\n    assert True\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "audit base")
    return git(root, "rev-parse", "HEAD")
def passing(root):
    obs = source_files(root)
    return Evidence(Kind.SUITE, "pytest tests", Result.PASS, obs,
                    tree_hash(root, obs), passed=1, counted=True, scope="source")
with tempfile.TemporaryDirectory(prefix="ep-audit-probes-", dir=str(Path.cwd())) as tmp:
    root = Path(tmp)
    base = setup(root)
    cmd = f"{sys.executable} -m pytest -q -x tests"
    (root / "tests/test_a.py").write_text("def test_a():\n    assert False\n")
    (root / "tests/test_b.py").write_text(
        "from pathlib import Path\n"
        "def test_b():\n    Path('executed-b').write_text('yes')\n    assert True\n")
    (root / "tests/test_c.py").write_text("def test_c():\n    assert True\n")
    led = Ledger(root, task="confirm", base=base,
                 failed_before=["tests/test_a.py::test_a", "tests/test_b.py::test_b", "tests/test_c.py::test_c"],
                 _config=Config(commands={"tests": cmd}))
    records = stress.confirm(led)
    led.add(records)
    shown, grain = led._reproduction()
    emit("confirm_fail_fast", records=[(r.identity, r.result.value) for r in records],
         second_test_executed=(root / "executed-b").exists(),
         reproduction=shown.identity if shown else None)
    (root / "tests/test_a.py").write_text(
        "import pytest\n@pytest.mark.skip(reason='audit')\ndef test_a():\n    assert False\n")
    led = Ledger(root, task="skip", base=base,
                 failed_before=["tests/test_a.py::test_a"],
                 _config=Config(commands={"tests": f"{sys.executable} -m pytest -q tests"}))
    records = stress.confirm(led)
    led.add(records)
    shown, _ = led._reproduction()
    emit("confirm_skip", records=[(r.identity, r.result.value) for r in records],
         reproduction=shown.identity if shown else None)
    (root / "tests/test_a.py").write_text("def test_a():\n    assert True\n")
    led = Ledger(root, task="cache", base=base, touched=["tests/test_a.py"],
                 evidence=[passing(root)],
                 _config=Config(commands={"tests": f"{sys.executable} -m pytest -q tests/test_a.py"}))
    led.discrimination, led.failed_before = stress.stress(led)
    first = dict(led.discrimination)
    (root / "app.py").write_text("value = 2\n")
    (root / "tests/test_a.py").write_text("from app import value\ndef test_a():\n    assert value == 2\n")
    cached, red = stress.stress(led)
    control = stress.on_the_old_tree(root, base, led.config.commands["tests"],
                                    carry=("tests/test_a.py",))
    emit("stress_cache_after_test_edit", initial=first, cached=cached,
         fresh_control_passes=control[0] if control else None)
    led = Ledger(root, task="question", base=base, request="refactor the function",
                 claims=[Claim.REFACTOR_SAFE], _config=Config(profile="off"))
    before = led.status().value
    with patch.object(Ledger, "load", return_value=led), patch.object(Ledger, "save"):
        rc = hook.on_stop({"last_assistant_message": "Which behavior do you want?"}, root)
    emit("question_creates_proven_snapshot", status_before=before,
         evidence_count=len(led.evidence), snapshot=bool(ratchet.proven(root, "question")),
         stop_return=rc)
    led = Ledger(root, task="output", base=base)
    with patch.object(Ledger, "load", return_value=led), patch.object(Ledger, "save"):
        hook.on_post_tool({"tool_name": "Bash",
                           "tool_input": {"command": "node -e \"console.log('producer sample')\""},
                           "tool_response": {"stdout": "producer sample\n", "stderr": ""}}, root)
    emit("ordinary_producer_output_dropped", captured_outputs=len(led.outputs))
    led = Ledger(root, base=base, touched=["tests/test_b.py"],
                 discrimination={"tests": "yes"},
                 failed_before=["tests/test_a.py::test_a"])
    emit("vacuous_from_absence", reported=assumptions.vacuous_tests(led))
    tap = parsers.parse("cat fixture.tap", "TAP version 13\nok 1 - sample\n1..1\n", 0, root)
    emit("reading_tap_file", records=[(r.kind.value, r.result.value, r.ran_tests) for r in tap])
    (root / "app.py").write_text("value = 1\n")
    emit("unchanged_file_marked_changed", git_diff=git(root, "diff", base, "--", "app.py"),
         changed_lines=sorted(radius.changed_lines(root, base, "app.py")))
    led = Ledger(root, task="off-execution", base=base, request="refactor",
                 claims=[Claim.REFACTOR_SAFE], evidence=[passing(root)],
                 _config=Config(profile="off", commands={"tests": "pytest tests"}))
    with patch.object(Ledger, "load", return_value=led), patch.object(Ledger, "save"), \
         patch.object(stress, "on_the_old_tree", return_value=(True, "1 passed in 0.01s")) as run:
        hook.on_stop({"last_assistant_message": "Done."}, root)
        emit("off_profile_replays_commands", command_calls=run.call_count)
    led = Ledger(root, task="unrelated", base=base, evidence=[passing(root)],
                 discrimination={"typecheck": "yes"})
    shown, grain = led._reproduction()
    emit("different_check_kinds_form_reproduction", reproduction=bool(shown), caveat=grain)
    (root / "uses.py").write_text("from app import value\n")
    led = Ledger(root, task="brief", base=base)
    edit = {"tool_name": "Edit", "tool_input": {"file_path": str(root / "app.py")}}
    with patch.object(Ledger, "load", return_value=led), patch.object(Ledger, "save"):
        no_read = io.StringIO()
        with contextlib.redirect_stdout(no_read):
            hook.on_pre_tool(edit, root)
        hook.on_post_tool({"tool_name": "Read",
                           "tool_input": {"file_path": str(root / "app.py")}}, root)
        after_read = io.StringIO()
        with contextlib.redirect_stdout(after_read):
            hook.on_pre_tool(edit, root)
    emit("read_then_edit_suppresses_brief", before_read=bool(no_read.getvalue()),
         after_read=bool(after_read.getvalue()))
    checkpoint = ratchet.snapshot(root, "restore", "audit snapshot")
    (root / "tests/test_later.py").write_text("def test_later():\n    assert False\n")
    git(root, "restore", f"--source={checkpoint}", "--worktree", "--", ".")
    emit("restore_leaves_new_test", extra_test_survives=(root / "tests/test_later.py").exists(),
         still_differs=ratchet.differs(root, checkpoint))
    fake = "ghp_AUDITONLY0000000000000000000000"
    led = Ledger(root, task="redact", base=base)
    with patch.object(Ledger, "load", return_value=led), patch.object(Ledger, "save"):
        hook.on_post_tool({"tool_name": "Bash",
                           "tool_input": {"command": "python -m pytest tests -q"},
                           "tool_response": {"stdout": "1 passed in 0.01s\n" + fake, "stderr": ""}}, root)
    emit("evidence_bypasses_output_redaction", token_in_outputs=fake in json.dumps(led.outputs),
         token_in_evidence=fake in json.dumps([r.to_dict() for r in led.evidence]))
rows = [("first", "task", "vanilla", "resolved", 1),
        ("second", "task", "vanilla", "unfixed", 2)]
emit("pooled_overwrites_sweeps", measured=measure(pools(rows), None, "vanilla"))
```

## Statistical arithmetic

For a binomial observation of one event in 22 independent trials, the exact upper confidence limit solves `P(X <= 1 | p) = alpha`. This gives **19.8122%** for a one-sided 95% bound and **22.8444%** for the upper end of a two-sided 95% interval. The B3/B4 observations actually share tasks and differ in model/configuration, so these calculations explain the arithmetic error; they do not validate independent pooling of those runs.

```python
from math import comb

def upper(k, n, alpha):
    lo, hi = 0.0, 1.0
    for _ in range(100):
        p = (lo + hi) / 2
        mass = sum(comb(n, j) * p**j * (1-p)**(n-j)
                   for j in range(k + 1))
        if mass > alpha:
            lo = p
        else:
            hi = p
    return (lo + hi) / 2

print(upper(1, 22, .05))   # 0.19812213163688158
print(upper(1, 22, .025))  # 0.22844439766763341
print(2 / 2**6)           # 0.03125: six independent discordances, all favorable
```

The 6-versus-0 calculation is a fixed-sample example, not a recommendation to repeatedly inspect results and stop at significance.

## Scope and limits

The probes establish specific counterexamples and control-flow defects. They do not establish their prevalence in production or invalidate every archived verdict. Existing B3/B4 summaries need a provenance and outcome audit before affected historical rates can be recomputed. The evidence ledger is not a full execution transcript, and some necessary historical facts may be unrecoverable.

The main report separates these reproduced defects from static architectural observations, already acknowledged limitations, and proposed research directions.

