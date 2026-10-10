"""A behaviour claim verified on a change that touched no test says so.

Measured 2026-10-10 (`results/reverted/`): 7 of the 8 vacuous agent checks came
from patches touching no test file, and replaying two of those runs through the
current runtime reached plain VERIFIED. Reported, not blocked: PLAN §5.12 asks
a refusal to earn its cost separately.
"""

from __future__ import annotations

import time

import pytest

from core.evidence import Evidence, Kind, Result, source_files, tree_hash
from core.ledger import UNTESTED, Ledger, Status
from core.obligations import Claim, Risk
from core.report import end_report


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "auth.py").write_text("def login():\n    return True\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_auth.py").write_text("def test_login():\n    assert True\n")
    return tmp_path


def _green(repo, claim, touched):
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[claim], risk=Risk.LOW)
    led.touched = list(touched)
    led.add([
        Evidence(Kind.TEST, "tests/test_auth.py::test_login", Result.PASS, files, tree, at=time.time()),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, passed=1, counted=True, at=time.time()),
    ])
    return led


@pytest.mark.parametrize("claim", [Claim.BUG_FIXED, Claim.FEATURE_ADDED])
def test_a_behaviour_claim_on_an_untested_change_is_qualified_not_refused(repo, claim):
    led = _green(repo, claim, ["src/auth.py"])
    assert led.status() is Status.VERIFIED
    met = [c for c in led.verdicts()[0].checks if c.met]
    assert met and all(UNTESTED in c.caveat for c in met)
    assert UNTESTED in end_report(led)


@pytest.mark.parametrize("claim", [Claim.BUG_FIXED, Claim.FEATURE_ADDED])
def test_a_written_test_removes_the_qualification(repo, claim):
    led = _green(repo, claim, ["src/auth.py", "tests/test_auth.py"])
    assert led.status() is Status.VERIFIED
    assert not any(UNTESTED in c.caveat for c in led.verdicts()[0].checks)
    assert UNTESTED not in end_report(led)


def test_an_emptied_test_file_is_not_a_written_test(repo):
    (repo / "tests" / "test_auth.py").write_text("# nothing left\n")
    led = _green(repo, Claim.FEATURE_ADDED, ["src/auth.py", "tests/test_auth.py"])
    assert any(UNTESTED in c.caveat for c in led.verdicts()[0].checks)


def test_an_earlier_qualification_is_kept_alongside(repo):
    """A suite red before and no redder now already says so; that must survive."""
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.FEATURE_ADDED], risk=Risk.LOW)
    led.touched = ["src/auth.py"]
    for at in (time.time() - 10, time.time()):
        led.add([
            Evidence(Kind.SUITE, "tests", Result.FAIL, files, tree, passed=3, failed=1, counted=True, at=at),
            Evidence(Kind.TEST, "tests/test_auth.py::test_old", Result.FAIL, files, tree, at=at),
        ])
    (suite,) = [c for c in led.verdicts()[0].checks if c.met]
    assert "no new failures" in suite.caveat and UNTESTED in suite.caveat


def test_a_refactor_is_not_asked_for_new_tests(repo):
    """Existing tests still passing is exactly what a refactor claims."""
    led = _green(repo, Claim.REFACTOR_SAFE, ["src/auth.py"])
    assert led.status() is Status.VERIFIED
    assert not any(UNTESTED in c.caveat for c in led.verdicts()[0].checks)


def test_an_unmet_check_is_left_to_say_what_is_missing(repo):
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    led.touched = ["src/auth.py"]
    assert led.status() is Status.UNVERIFIED
    assert not any(UNTESTED in c.caveat for c in led.verdicts()[0].checks)
