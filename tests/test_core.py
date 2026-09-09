import time
from pathlib import Path

import pytest

from core.evidence import Evidence, Freshness, Kind, Result, source_files, tree_hash
from core.ledger import Ledger, Status
from core.obligations import Claim, Risk, risk_of
from core.parsers import parse
from core.report import end_report, gate_message


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "auth.py").write_text("def login():\n    return True\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_auth.py").write_text("def test_login():\n    assert True\n")
    return tmp_path


def test_tree_hash_changes_with_content(repo):
    files = source_files(repo)
    before = tree_hash(repo, files)
    (repo / "src" / "auth.py").write_text("def login():\n    return False\n")
    assert tree_hash(repo, files) != before


def test_evidence_goes_stale_on_edit(repo):
    files = source_files(repo)
    ev = Evidence(Kind.SUITE, "tests", Result.PASS, files, tree_hash(repo, files))
    assert ev.freshness(repo) is Freshness.FRESH
    (repo / "src" / "auth.py").write_text("changed\n")
    assert ev.freshness(repo) is Freshness.STALE


def test_evidence_gone_when_file_removed(repo):
    files = source_files(repo)
    ev = Evidence(Kind.SUITE, "tests", Result.PASS, files, tree_hash(repo, files))
    (repo / "src" / "auth.py").unlink()
    assert ev.freshness(repo) is Freshness.GONE


PYTEST_OUT = """
tests/test_auth.py::test_login PASSED
tests/test_auth.py::test_race FAILED
=================== 1 failed, 1 passed in 0.30s ===================
"""


def test_pytest_parser_extracts_nodes_and_suite(repo):
    records = parse("pytest tests/", PYTEST_OUT, 1, repo)
    kinds = [r.kind for r in records]
    assert Kind.TEST in kinds and Kind.SUITE in kinds
    suite = [r for r in records if r.kind is Kind.SUITE][0]
    assert (suite.passed, suite.failed) == (1, 1)
    assert suite.result is Result.FAIL


def test_jest_parser_counts(repo):
    out = "Tests:       2 failed, 5 passed, 7 total\n"
    records = parse("npx jest", out, 1, repo)
    assert (records[0].passed, records[0].failed) == (5, 2)


def test_tsc_parser_counts_errors(repo):
    out = "src/a.ts(3,10): error TS2345: bad\nFound 1 error.\n"
    records = parse("npx tsc --noEmit", out, 2, repo)
    assert records[0].kind is Kind.TYPECHECK and records[0].failed == 1


def test_unknown_command_yields_nothing(repo):
    assert parse("ls -la", "whatever", 0, repo) == []


def test_risk_high_on_auth_paths():
    risk, domains = risk_of(["src/auth/session.py"])
    assert risk is Risk.HIGH and domains == ["auth"]


def test_risk_low_on_small_ordinary_change():
    assert risk_of(["src/button.css"])[0] is Risk.LOW


def test_unverified_until_obligations_met(repo):
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    assert led.status() is Status.UNVERIFIED
    assert "missing" in gate_message(led)


def test_verified_when_obligations_met(repo):
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    led.add([
        Evidence(Kind.TEST, "tests/test_auth.py::test_race", Result.PASS, files, tree, at=time.time()),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=time.time()),
    ])
    assert led.status() is Status.VERIFIED
    assert gate_message(led) == ""


def test_edit_after_green_makes_it_stale(repo):
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    led.add([
        Evidence(Kind.TEST, "t::a", Result.PASS, files, tree, command="pytest", at=time.time()),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, command="pytest", at=time.time()),
    ])
    assert led.status() is Status.VERIFIED
    (repo / "src" / "auth.py").write_text("def login():\n    return None\n")
    assert led.status() is Status.STALE
    assert "stale" in gate_message(led)


def test_fresh_failure_contradicts(repo):
    """A suite that was green and is now red is our fault, so it contradicts."""
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    led.add([
        Evidence(Kind.TEST, "t::a", Result.PASS, files, tree, at=1.0),
        Evidence(Kind.SUITE, "other", Result.PASS, files, tree, at=1.0),
        Evidence(Kind.SUITE, "other", Result.FAIL, files, tree, at=2.0),
    ])
    assert led.status() is Status.CONTRADICTED


def test_pre_existing_failure_does_not_contradict(repo):
    """A suite that was already red when the task began is not ours to answer for."""
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    led.add([
        Evidence(Kind.SUITE, "other", Result.FAIL, files, tree, at=1.0),
        Evidence(Kind.SUITE, "tests/test_auth.py", Result.PASS, files, tree, at=2.0),
        Evidence(Kind.SUITE, "other", Result.FAIL, files, tree, at=3.0),
    ])
    assert led.status() is not Status.CONTRADICTED
    assert [e.identity for e in led.pre_existing()] == ["other"]


def test_high_risk_demands_prior_failure(repo):
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.HIGH)
    now = time.time()
    led.add([
        Evidence(Kind.TEST, "t::a", Result.PASS, files, tree, at=now),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=now),
    ])
    missing = {c.obligation.key for v in led.verdicts() for c in v.missing}
    assert "reproduced" in missing


def test_stability_demanded_only_for_intermittent_requests(repo):
    """Repeated-run evidence is expensive; it needs a reason, not a risk tier."""
    files = source_files(repo)
    tree = tree_hash(repo, files)
    plain = Ledger(root=repo, request="fix the login bug", claims=[Claim.BUG_FIXED], risk=Risk.HIGH)
    flaky = Ledger(root=repo, request="fix the intermittent race in login",
                   claims=[Claim.BUG_FIXED], risk=Risk.HIGH)
    for led in (plain, flaky):
        led.add([Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=1.0)])
    keys = lambda l: {c.obligation.key for v in l.verdicts() for c in v.checks}
    assert "stable" not in keys(plain)
    assert "stable" in keys(flaky)


def test_reproduction_recognised_when_failure_precedes_pass(repo):
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.MEDIUM)
    led.add([
        Evidence(Kind.TEST, "t::a", Result.FAIL, files, tree, at=1.0),
        Evidence(Kind.TEST, "t::a", Result.PASS, files, tree, at=2.0),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=2.0),
    ])
    missing = {c.obligation.key for v in led.verdicts() for c in v.missing}
    assert "reproduced" not in missing


def test_docs_claim_needs_nothing(repo):
    led = Ledger(root=repo, claims=[Claim.DOCS_CHANGED], risk=Risk.LOW)
    assert led.status() is Status.VERIFIED


def test_no_claim_means_no_gate(repo):
    assert Ledger(root=repo).status() is Status.VERIFIED


def test_ledger_round_trips(repo):
    files = source_files(repo)
    led = Ledger(root=repo, request="fix the race", claims=[Claim.BUG_FIXED], risk=Risk.HIGH,
                 domains=["auth"], allow=["src/auth/**"])
    led.add([Evidence(Kind.SUITE, "tests", Result.PASS, files, tree_hash(repo, files), at=1.0)])
    led.note("gate blocked", "reproduction missing")
    led.save()
    back = Ledger.load(repo)
    assert back.claims == [Claim.BUG_FIXED]
    assert back.risk is Risk.HIGH
    assert back.evidence[0].identity == "tests"
    assert back.decisions[0]["what"] == "gate blocked"


def test_end_report_mentions_status_and_counts(repo):
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    led.add([
        Evidence(Kind.TEST, "t::a", Result.PASS, files, tree, at=1.0),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=1.0),
    ])
    text = end_report(led)
    assert "VERIFIED" in text and "evidence: 2 record(s)" in text


def test_superseded_failure_is_reproduction_not_contradiction(repo):
    """A test that failed then passed is the reproduction, not a contradiction."""
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.MEDIUM)
    led.add([
        Evidence(Kind.SUITE, "tests/test_auth.py", Result.FAIL, files, tree, at=1.0),
        Evidence(Kind.SUITE, "tests/test_auth.py", Result.PASS, files, tree, at=2.0),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=3.0),
    ])
    assert led.status() is Status.VERIFIED


def test_still_failing_test_contradicts(repo):
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    led.add([
        Evidence(Kind.SUITE, "tests/test_auth.py", Result.PASS, files, tree, at=1.0),
        Evidence(Kind.SUITE, "tests/test_auth.py", Result.FAIL, files, tree, at=2.0),
    ])
    assert led.status() is Status.CONTRADICTED


def test_scoped_obligation_accepts_a_test_file_run(repo):
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    led.add([
        Evidence(Kind.SUITE, "tests/test_auth.py", Result.PASS, files, tree, at=1.0),
        Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=1.0),
    ])
    assert led.status() is Status.VERIFIED


def test_whole_suite_alone_does_not_prove_a_covering_test(repo):
    files = source_files(repo)
    tree = tree_hash(repo, files)
    led = Ledger(root=repo, claims=[Claim.BUG_FIXED], risk=Risk.LOW)
    led.add([Evidence(Kind.SUITE, "tests", Result.PASS, files, tree, at=1.0)])
    missing = {c.obligation.key for v in led.verdicts() for c in v.missing}
    assert "test_added" in missing
