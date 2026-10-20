"""Python's standard unittest summary is read from actual runs, never from a file's shape."""
import subprocess
import sys

import pytest

from core.config import Config, save
from core.evidence import Kind, Result
from core.parsers import parse

BODIES = {
    "pass": "    def test_a(self):\n        self.assertTrue(True)\n    def test_b(self):\n        self.assertTrue(True)\n",
    "fail": "    def test_a(self):\n        self.assertTrue(True)\n    def test_b(self):\n        self.assertEqual(1, 2)\n",
    "error": "    def test_a(self):\n        raise RuntimeError('boom')\n    def test_b(self):\n        self.assertEqual(1, 2)\n",
    "skip": "    @unittest.skip('later')\n    def test_a(self):\n        pass\n    def test_b(self):\n        self.assertTrue(True)\n",
    "expected-failure": "    @unittest.expectedFailure\n    def test_a(self):\n        self.assertEqual(1, 2)\n"
                        "    def test_b(self):\n        self.assertTrue(True)\n",
    "unexpected-success": "    @unittest.expectedFailure\n    def test_a(self):\n        self.assertTrue(True)\n",
}
COMMAND = f'"{sys.executable}" -m unittest discover -s tests'


def _run(root, body):
    (root / "tests").mkdir(exist_ok=True)
    if body is not None:
        (root / "tests" / "test_x.py").write_text("import unittest\nclass T(unittest.TestCase):\n" + body,
                                                    encoding="utf8")
    done = subprocess.run(COMMAND, cwd=root, shell=True, capture_output=True, text=True, timeout=60)
    return done.stdout + done.stderr, done.returncode


@pytest.mark.parametrize("shown", [COMMAND, COMMAND + " -v 2>&1 | tail -15"], ids=["plain", "filtered"])
@pytest.mark.parametrize("case, passed, failed, result", [
    ("pass", 2, 0, Result.PASS), ("fail", 1, 1, Result.FAIL), ("error", 0, 2, Result.FAIL),
    ("skip", 1, 0, Result.PASS), ("expected-failure", 1, 0, Result.PASS),
    ("unexpected-success", 0, 1, Result.FAIL),
])
def test_actual_unittest_summary_is_a_counted_suite(tmp_path, shown, case, passed, failed, result):
    output, code = _run(tmp_path, BODIES[case])
    # A filter's own exit status replaces the runner's; the counted summary must still decide.
    records = parse(shown, output, 0 if "tail" in shown else code, tmp_path)

    assert [(r.kind, r.counted, r.passed, r.failed, r.result, r.ran_tests) for r in records] == [
        (Kind.SUITE, True, passed, failed, result, True)]


def test_actual_run_with_no_tests_is_not_suite_proof(tmp_path):
    output, code = _run(tmp_path, None)

    (record,) = parse(COMMAND, output, code, tmp_path)
    assert record.kind is Kind.SUITE and not record.ran_tests


def test_unittest_summary_from_a_command_that_runs_no_tests_is_not_evidence(tmp_path):
    output, _ = _run(tmp_path, BODIES["pass"])
    (tmp_path / "old.log").write_text(output, encoding="utf8")

    assert parse("cat old.log", output, 0, tmp_path) == []
    assert parse("type old.log", output, 0, tmp_path) == []


def test_named_unittest_without_a_summary_is_not_suite_proof(tmp_path):
    (record,) = parse(COMMAND + " 2>&1 | tail -1", "OK\n", 0, tmp_path)

    assert record.kind is Kind.SUITE and not record.ran_tests


def test_declared_unittest_counts_failures_errors_and_unexpected_successes(tmp_path):
    save(tmp_path, Config(profile="guide", auto_detect=False, commands={"tests": COMMAND}))
    output, code = _run(tmp_path, BODIES["error"])

    (record,) = parse(COMMAND, output, code, tmp_path)
    assert record.declaration == "tests" and record.counted
    assert (record.passed, record.failed, record.result) == (0, 2, Result.FAIL)


def test_filtered_unittest_leaves_exact_declaration_stale_and_offers_owned_runner(tmp_path):
    from core.check_feedback import feedback
    from core.ledger import Ledger

    save(tmp_path, Config(profile="guide", auto_detect=False, commands={"tests": COMMAND}))
    output, code = _run(tmp_path, BODIES["pass"])
    ledger = Ledger(root=tmp_path, task="unittest-feedback")
    ledger.add(parse(COMMAND, output, code, tmp_path))
    ledger.save()
    (tmp_path / "tests" / "test_x.py").write_text("import unittest\nclass T(unittest.TestCase):\n" + BODIES["skip"],
                                                  encoding="utf8")
    output, code = _run(tmp_path, None)
    generic = parse(COMMAND + " -v 2>&1 | tail -15", output, 0, tmp_path)

    text = feedback(Ledger.load(tmp_path), generic, COMMAND + " -v 2>&1 | tail -15")
    assert "Owned check arguments:" in text


def test_a_failure_in_an_earlier_unittest_summary_is_not_hidden_by_a_later_pass(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    failing, _ = _run(tmp_path / "a", BODIES["fail"])
    passing, _ = _run(tmp_path / "b", BODIES["pass"])

    (record,) = parse(COMMAND + " && " + COMMAND, failing + passing, 0, tmp_path)
    assert (record.passed, record.failed, record.result) == (3, 1, Result.FAIL)


def test_declared_wrapper_that_runs_unittest_is_counted(tmp_path):
    (tmp_path / "check.py").write_text(
        "import sys, unittest\n"
        "suite = unittest.defaultTestLoader.discover('tests')\n"
        "sys.exit(not unittest.TextTestRunner().run(suite).wasSuccessful())\n", encoding="utf8")
    command = f'"{sys.executable}" check.py'
    save(tmp_path, Config(profile="guide", auto_detect=False, commands={"tests": command}))
    _run(tmp_path, BODIES["error"])
    done = subprocess.run(command, cwd=tmp_path, shell=True, capture_output=True, text=True, timeout=60)

    (record,) = parse(command, done.stdout + done.stderr, done.returncode, tmp_path)
    assert record.counted and (record.passed, record.failed, record.result) == (0, 2, Result.FAIL)
