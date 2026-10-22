"""pytest 9 prints PASSED for a test whose subtests failed, and one SUBFAILED line per failure.

The lines below are copied from pycparser's suite under pytest 9.1.1 on 2026-10-22.
"""
import sys

from tests.test_heldout_grading import _task

REAL = (
    "PASSED tests/test_c_parser.py::TestCParser_dialects::test_c23_unsupported_keywords_are_reserved\n"
    "SUBFAILED(source='_Decimal32 x;') tests/test_c_parser.py::TestCParser_dialects::test_c23_unsupported_keywords_are_reserved\n"
    "SUBFAILED(source='_Decimal64 x;') tests/test_c_parser.py::TestCParser_dialects::test_c23_unsupported_keywords_are_reserved\n"
    "PASSED tests/test_c_parser.py::TestCParser_dialects::test_c11_keywords\n"
)
PARTIAL = "tests/test_c_parser.py::TestCParser_dialects::test_c23_unsupported_keywords_are_reserved"


def test_a_test_with_a_failed_subtest_did_not_pass():
    from eval.mine import passing_nodes
    assert passing_nodes(REAL) == {"tests/test_c_parser.py::TestCParser_dialects::test_c11_keywords"}


def test_a_test_with_a_failed_subtest_is_named_as_failing():
    from eval.mine import failing_nodes
    assert failing_nodes(REAL) == [PARTIAL]


SUBTEST = ("import unittest\n\nfrom pkg.mod import value\n\n\nclass TestNew(unittest.TestCase):\n"
           "    def test_new(self):\n        with self.subTest(case='two'):\n            self.assertEqual(value(), 2)\n")


def test_grading_does_not_credit_a_required_test_whose_subtest_fails(tmp_path):
    from eval.live import grade_patch
    task, gold = _task(tmp_path)
    task.source["hidden_files"] = {"test/test_new.py": SUBTEST}
    task.source["f2p"] = ["test/test_new.py::TestNew::test_new"]
    assert grade_patch(task, "", tmp_path / "base").outcome == "unfixed"
    assert grade_patch(task, gold, tmp_path / "gold").outcome == "resolved"


def test_the_vacuity_probe_deselects_a_test_red_only_through_subtests(tmp_path):
    from eval.heldout_vacuity import vacuity
    from tests.test_heldout_vacuity import SOURCE, _base
    base = _base(tmp_path / "base")
    pinned_old = SUBTEST.replace("value(), 2", "value(), 1").replace("TestNew", "TestOld")
    (base / "tests" / "test_sub.py").write_text(pinned_old, encoding="utf8", newline="\n")
    value = vacuity(base, SOURCE, python=sys.executable, env={"PYTHONPATH": "."}, test_dir="tests", work=tmp_path / "work")
    assert value == {"vacuous": True, "reason": "revert survived"}
