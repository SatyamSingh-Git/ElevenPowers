import subprocess
import sys
import time
from pathlib import Path

import pytest

from core.evidence import Evidence, Kind, Result, source_files, tree_hash
from core.ledger import Ledger, Status
from core.obligations import Claim, Risk
from core.parsers import parse
from core.repeat import MAX_RUNS, MIN_RUNS, rules_out, run, runs_needed
from core.report import gate_message

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "worker.py").write_text("x = 1\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_race.py").write_text("def test_r():\n    assert True\n")
    for args in (["init", "-q"], ["add", "-A"],
                 ["-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", "b"]):
        subprocess.run(["git", *args], cwd=tmp_path, capture_output=True)
    return tmp_path


def stability(repo, runs, failed, at=1.0, identity="pytest tests/test_race.py"):
    files = source_files(repo)
    return Evidence(
        kind=Kind.STABILITY, identity=identity,
        result=Result.PASS if failed == 0 else Result.FAIL,
        observed=files, tree=tree_hash(repo, files),
        command=f"ep-repeat {runs} -- {identity}",
        runs=runs, passed=runs - failed, failed=failed, at=at,
    )


# --- the arithmetic -------------------------------------------------------

def test_rarer_failures_need_more_runs():
    assert runs_needed(0.5) < runs_needed(0.1) < runs_needed(0.02)


def test_run_count_matches_the_confidence_formula():
    # A 6% failure rate survives 48 clean runs with probability 0.94**48, just
    # under 5%, so 49 runs is where 95% confidence is reached.
    assert runs_needed(0.06, confidence=0.95) == 49
    assert 0.94 ** 48 > 0.05 > 0.94 ** 49


def test_run_count_is_bounded_at_both_ends():
    assert runs_needed(0.999) == MIN_RUNS or runs_needed(0.999) >= 1
    assert runs_needed(0.0001) == MAX_RUNS
    assert runs_needed(0.0) == MIN_RUNS


def test_rules_out_inverts_runs_needed():
    rate = rules_out(50)
    assert runs_needed(rate) <= 50 + 1


# --- the runner -----------------------------------------------------------

def test_runner_counts_a_command_that_always_passes(tmp_path):
    outcome = run(f'"{sys.executable}" -c "pass"', 5, tmp_path)
    assert (outcome.runs, outcome.passed, outcome.failed) == (5, 5, 0)
    assert outcome.verdict == "stable"


def test_runner_counts_a_command_that_always_fails(tmp_path):
    outcome = run(f'"{sys.executable}" -c "raise SystemExit(1)"', 3, tmp_path)
    assert outcome.failed == 3 and outcome.verdict == "always-fails"


def test_runner_detects_a_genuinely_flaky_command(tmp_path):
    """A command failing on a fixed fraction of runs is reported as flaky."""
    script = tmp_path / "flaky.py"
    script.write_text(
        "import pathlib, sys\n"
        "c = pathlib.Path('count.txt')\n"
        "n = int(c.read_text()) if c.exists() else 0\n"
        "c.write_text(str(n + 1))\n"
        "sys.exit(1 if n % 4 == 0 else 0)\n"
    )
    outcome = run(f'"{sys.executable}" flaky.py', 12, tmp_path)
    assert outcome.verdict == "flaky"
    assert outcome.failed == 3 and outcome.passed == 9
    assert 0.2 < outcome.rate < 0.3


def test_runner_stops_early_when_asked(tmp_path):
    outcome = run(f'"{sys.executable}" -c "raise SystemExit(1)"', 50, tmp_path,
                  stop_on_fail=True)
    assert outcome.runs == 1 and outcome.stopped_early


def test_runner_runs_in_parallel(tmp_path):
    outcome = run(f'"{sys.executable}" -c "import time; time.sleep(0.3)"', 6,
                  tmp_path, jobs=6)
    assert outcome.passed == 6 and outcome.seconds < 1.6


def test_runner_treats_a_timeout_as_failure(tmp_path):
    outcome = run(f'"{sys.executable}" -c "import time; time.sleep(5)"', 1,
                  tmp_path, timeout=1)
    assert outcome.failed == 1


def test_cli_reports_and_exits_nonzero_on_failure(tmp_path):
    done = subprocess.run(
        [sys.executable, str(REPO_ROOT / "plugin" / "bin" / "ep_repeat.py"),
         "3", "--cwd", str(tmp_path), "--", sys.executable, "-c", "raise SystemExit(1)"],
        capture_output=True, text=True,
    )
    assert done.returncode == 1
    assert "EP-REPEAT verdict=always-fails runs=3" in done.stdout


def test_cli_output_becomes_stability_evidence(tmp_path, repo):
    done = subprocess.run(
        [sys.executable, str(REPO_ROOT / "plugin" / "bin" / "ep_repeat.py"),
         "4", "--cwd", str(tmp_path), "--", sys.executable, "-c", "pass"],
        capture_output=True, text=True,
    )
    records = parse("ep-repeat 4 -- python -c pass", done.stdout, done.returncode, repo)
    assert len(records) == 1
    assert records[0].kind is Kind.STABILITY
    assert records[0].runs == 4 and records[0].failed == 0


# --- the obligation -------------------------------------------------------

def test_one_lucky_run_no_longer_proves_stability(repo):
    """The defect this was built for: a single clean execution is not proof."""
    request = "fix the intermittent race in the worker"
    led = Ledger(root=repo, request=request, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led.add([
        Evidence(Kind.RUNTIME, "repro.py", Result.PASS, files, tree,
                 command="python repro.py", at=1.0),
        Evidence(Kind.SUITE, "tests/test_race.py", Result.FAIL, files, tree, at=2.0),
        Evidence(Kind.SUITE, "tests/test_race.py", Result.PASS, files, tree, at=3.0),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=4.0),
    ])
    assert led.status() is Status.UNVERIFIED
    missing = {c.obligation.key for v in led.verdicts() for c in v.missing}
    assert missing == {"stable"}


def test_enough_clean_repeats_discharge_stability(repo):
    request = "fix the intermittent race in the worker"
    led = Ledger(root=repo, request=request, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led.add([
        Evidence(Kind.SUITE, "tests/test_race.py", Result.FAIL, files, tree, at=1.0),
        Evidence(Kind.SUITE, "tests/test_race.py", Result.PASS, files, tree, at=2.0),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=3.0),
        stability(repo, runs=MIN_RUNS, failed=0, at=4.0),
    ])
    assert led.status() is Status.VERIFIED


def test_too_few_repeats_are_rejected_with_the_shortfall(repo):
    request = "fix the flaky worker test"
    led = Ledger(root=repo, request=request, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led.add([
        Evidence(Kind.SUITE, "tests/test_race.py", Result.FAIL, files, tree, at=1.0),
        Evidence(Kind.SUITE, "tests/test_race.py", Result.PASS, files, tree, at=2.0),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=3.0),
        stability(repo, runs=5, failed=0, at=4.0),
    ])
    assert led.status() is Status.UNVERIFIED
    assert "5 clean runs, 20 needed" in gate_message(led)


def test_observed_failure_rate_raises_the_bar(repo):
    """Seeing the bug fail 3 times in 50 demands far more than the floor."""
    led = Ledger(root=repo, request="fix the intermittent race",
                 claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    led.add([stability(repo, runs=50, failed=3, at=1.0)])
    assert led.required_runs() == runs_needed(0.06) == 49


def test_repeats_that_still_fail_are_reported_as_such(repo):
    led = Ledger(root=repo, request="fix the intermittent race",
                 claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led.add([
        Evidence(Kind.SUITE, "tests/test_race.py", Result.FAIL, files, tree, at=1.0),
        Evidence(Kind.SUITE, "tests/test_race.py", Result.PASS, files, tree, at=2.0),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=3.0),
        stability(repo, runs=40, failed=2, at=4.0),
    ])
    assert "still failed 2 of 40" in gate_message(led)


def test_stability_evidence_goes_stale_like_any_other(repo):
    led = Ledger(root=repo, request="fix the intermittent race",
                 claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led.add([
        Evidence(Kind.SUITE, "tests/test_race.py", Result.FAIL, files, tree, at=1.0),
        Evidence(Kind.SUITE, "tests/test_race.py", Result.PASS, files, tree, at=2.0),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=3.0),
        stability(repo, runs=MIN_RUNS, failed=0, at=4.0),
    ])
    assert led.status() is Status.VERIFIED
    time.sleep(0.01)
    (repo / "src" / "worker.py").write_text("x = 2\n")
    assert led.status() is Status.STALE


def test_hint_names_the_command_that_failed(repo):
    led = Ledger(root=repo, request="fix the intermittent race",
                 claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led.add([
        Evidence(Kind.SUITE, "tests/test_race.py", Result.FAIL, files, tree,
                 command="pytest tests/test_race.py -q", at=1.0),
        Evidence(Kind.SUITE, "tests/test_race.py", Result.PASS, files, tree,
                 command="pytest tests/test_race.py -q", at=2.0),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree,
                 command="pytest tests/ -q", at=3.0),
    ])
    assert "ep-repeat 20 -- pytest tests/test_race.py -q" in gate_message(led)


def test_ordinary_bug_fix_never_asks_for_repeats(repo):
    led = Ledger(root=repo, request="fix the login bug",
                 claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    keys = {c.obligation.key for v in led.verdicts() for c in v.checks}
    assert "stable" not in keys
