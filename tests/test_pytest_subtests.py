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
# Every subTest form pytest 9.1.1 printed for a scratch suite on 2026-10-22, including a
# message, a message with parameters, and parameters that contain ") " and "::".
FORMS = (
    "PASSED tests/test_forms.py::T::test_both\n"
    "PASSED tests/test_forms.py::T::test_msgonly\n"
    "PASSED tests/test_forms.py::T::test_ok\n"
    "PASSED tests/test_forms.py::T::test_params\n"
    "PASSED tests/test_forms.py::T::test_paren\n"
    "SUBFAILED[a message] (i=1) tests/test_forms.py::T::test_both - AssertionError: b\n"
    "SUBFAILED[plain] tests/test_forms.py::T::test_msgonly - AssertionError: m\n"
    "SUBFAILED(source='int x;') tests/test_forms.py::T::test_params - AssertionErr...\n"
    "SUBFAILED(p='x) y::z') tests/test_forms.py::T::test_paren - AssertionError: q\n"
    "SUBFAILED[fx] (n=2) tests/test_forms.py::test_fixture - assert False\n"
    "FAILED tests/test_forms.py::test_fixture - contains 1 failed subtest\n"
    "PASSED tests/test_dash.py::D::test_dash\n"
    "SUBFAILED(p='a x::y - z') tests/test_dash.py::D::test_dash - AssertionError: d\n"
)
FORM_FAILURES = ["tests/test_forms.py::T::test_both", "tests/test_forms.py::T::test_msgonly",
                 "tests/test_forms.py::T::test_params", "tests/test_forms.py::T::test_paren",
                 "tests/test_forms.py::test_fixture", "tests/test_dash.py::D::test_dash"]


def test_a_test_with_a_failed_subtest_did_not_pass():
    from eval.mine import passing_nodes
    assert passing_nodes(REAL) == {"tests/test_c_parser.py::TestCParser_dialects::test_c11_keywords"}
    assert passing_nodes(FORMS) == {"tests/test_forms.py::T::test_ok"}


def test_a_test_with_a_failed_subtest_is_named_as_failing():
    from eval.mine import failing_nodes
    assert failing_nodes(REAL) == [PARTIAL]
    assert failing_nodes(FORMS) == FORM_FAILURES


def test_the_vacuity_reader_takes_the_node_and_not_a_parameter():
    from eval.heldout_vacuity import _red
    assert _red(FORMS) == set(FORM_FAILURES)


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


def test_the_runtime_records_a_test_whose_subtests_failed_as_failing(tmp_path):
    from core import parsers
    from core.evidence import Kind, Result
    records = parsers.parse("python -m pytest tests -q -rA", FORMS + "6 failed, 1 passed in 0.10s\n", 1, tmp_path)
    results = {r.identity: r.result for r in records if r.kind == Kind.TEST}
    assert results["tests/test_forms.py::T::test_ok"] == Result.PASS
    assert {node: results[node] for node in FORM_FAILURES} == {node: Result.FAIL for node in FORM_FAILURES}


def test_a_reproduction_is_not_credited_to_a_test_whose_subtests_failed():
    from core.stress import _passed
    assert _passed(FORMS) == {"tests/test_forms.py::T::test_ok"}
