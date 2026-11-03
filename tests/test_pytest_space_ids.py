"""A parametrised test id can hold spaces, " - " and "]"; the node is all of it.

Copied from pytest 9.1.1 on 2026-11-03, `-rA` and `-v`, for ids built from
"setting value", "a - b" and "x]y". Replaying v3 stages, confirmation named
`test_bad_settings_are_refused[raw4-setting`, which pytest cannot find.
"""
from core.parsers import parse

RA = (
    "=========================== short test summary info ===========================\n"
    "PASSED tests/test_space.py::test_param[setting value]\n"
    "PASSED tests/test_space.py::test_param[plain]\n"
    "PASSED tests/test_space.py::test_param[x]y]\n"
    "PASSED tests/test_space.py::test_objects[raw0]\n"
    "FAILED tests/test_space.py::test_param[a - b] - AssertionError: assert 'a - b...\n"
    "FAILED tests/test_space.py::test_plain - AssertionError: [x] - y\n"
    "FAILED tests/test_space.py::test_list[p] - AssertionError: assert [1] - [2]\n"
    "PASSED tests/test_space.py::Suite::test_method\n"
    "3 failed, 6 passed in 0.06s\n"
)
VERBOSE = (
    "tests/test_space.py::test_param[setting value] PASSED                    [ 16%]\n"
    "tests/test_space.py::test_param[a - b] FAILED                            [ 50%]\n"
    "tests/test_space.py::test_param[x]y] PASSED                              [ 66%]\n"
    "tests/test_space.py::Suite::test_plain PASSED                            [100%]\n"
)
NODES = {
    "tests/test_space.py::test_param[setting value]": "pass",
    "tests/test_space.py::test_param[plain]": "pass",
    "tests/test_space.py::test_param[x]y]": "pass",
    "tests/test_space.py::test_objects[raw0]": "pass",
    "tests/test_space.py::test_param[a - b]": "fail",
    "tests/test_space.py::test_plain": "fail",
    "tests/test_space.py::test_list[p]": "fail",
    "tests/test_space.py::Suite::test_method": "pass",
}


def _tests(output, tmp_path):
    return {e.identity: e.result.value for e in parse("python -m pytest -rA tests", output, 1, tmp_path)
            if e.kind.value == "test" and "::" in e.identity}


def test_summary_ids_keep_their_spaces_and_stop_before_the_message(tmp_path):
    assert _tests(RA, tmp_path) == NODES


def test_confirmation_reads_whole_passing_ids():
    # The sibling that stress.confirm reads; it left confirmation "incomplete" on v3 replays.
    from core.stress import _passed
    assert _passed(RA) == {node for node, result in NODES.items() if result == "pass"}


SUBTEST = (
    "PASSED tests/test_sub.py::test_ok[setting value]\n"
    "PASSED tests/test_sub.py::test_sub[setting value]\n"
    "SUBFAILED[inner one] (n=1) tests/test_sub.py::test_sub[setting value] - asser...\n"
)


def test_a_failed_subtest_takes_the_whole_id_with_it():
    from core.stress import _passed
    assert _passed(SUBTEST) == {"tests/test_sub.py::test_ok[setting value]"}


def test_verbose_ids_keep_their_spaces(tmp_path):
    assert _tests(VERBOSE, tmp_path) == {
        "tests/test_space.py::test_param[setting value]": "pass",
        "tests/test_space.py::test_param[a - b]": "fail",
        "tests/test_space.py::test_param[x]y]": "pass",
        "tests/test_space.py::Suite::test_plain": "pass",
    }
