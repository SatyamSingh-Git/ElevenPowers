"""Maven test runs: counted, failing tests named, a stopped build seen (captured 2026-11-25).

Fixtures are real Maven 3.9.9 output (JUnit 5.11.3; Surefire 3.5.2 and 2.22.2) with the
build folder replaced by C:\\project.
"""
from pathlib import Path

import pytest

from core import parsers
from core.evidence import Kind, Result

FIXTURES = Path(__file__).parent / 'fixtures' / 'maven'


def read(name):
    return (FIXTURES / name).read_text(encoding='utf-8')


def records(output, exit_code, tmp_path, command='mvn test'):
    found = parsers.parse(command, output, exit_code, tmp_path)
    tests = sorted((r.identity, r.result) for r in found if r.kind is Kind.TEST)
    suite = [r for r in found if r.kind is Kind.SUITE][-1]
    return tests, suite


@pytest.mark.parametrize('name', ['surefire3-fail.txt', 'surefire2-fail.txt', 'surefire3-quiet-fail.txt'])
def test_a_failing_run_is_counted_and_names_its_failures(tmp_path, name):
    tests, suite = records(read(name), 1, tmp_path)
    assert tests == [('CalcTest.throwsOnPurpose', Result.FAIL), ('CalcTest.wrongOnPurpose', Result.FAIL)]
    assert (suite.passed, suite.failed, suite.counted, suite.result) == (1, 2, True, Result.FAIL)


def test_a_passing_run_is_counted_and_names_nothing(tmp_path):
    tests, suite = records(read('surefire3-pass.txt'), 0, tmp_path)
    assert tests == []
    assert (suite.passed, suite.failed, suite.counted, suite.result) == (1, 0, True, Result.PASS)


def test_the_counts_outrank_an_exit_code_a_pipe_swallowed(tmp_path):
    _, suite = records(read('surefire3-fail.txt'), 0, tmp_path, 'mvn test | tail -40')
    assert suite.result is Result.FAIL


def test_two_modules_are_summed(tmp_path):
    tests, suite = records(read('two-modules-fail-at-end.txt'), 1, tmp_path, 'mvn test -fae')
    assert (suite.passed, suite.failed) == (3, 2)
    assert [name for name, _ in tests] == ['CalcTest.throwsOnPurpose', 'CalcTest.wrongOnPurpose']


def test_an_indented_info_line_is_never_a_test(tmp_path):
    output = read('surefire3-pass.txt')
    assert '[INFO]   from pom.xml' in output
    assert records(output, 0, tmp_path)[0] == []


def test_a_compile_is_a_build_not_a_test_run(tmp_path):
    found = parsers.parse('mvn -q compile', '', 0, tmp_path)
    assert not any(r.kind in (Kind.SUITE, Kind.TEST) for r in found)


def test_the_wrapper_and_a_build_with_no_test_summary(tmp_path):
    _, suite = records(read('surefire3-pass.txt'), 0, tmp_path, './mvnw test')
    assert suite.counted and suite.passed == 1
    compile_error = '[ERROR] COMPILATION ERROR :\n[INFO] BUILD FAILURE\n'
    tests, suite = records(compile_error, 1, tmp_path)
    assert tests == [] and not suite.counted and suite.result is Result.FAIL
