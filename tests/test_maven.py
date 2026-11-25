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


def test_a_build_that_skipped_a_module_stopped_before_every_test_ran():
    from core.review import STOPPED
    assert STOPPED.search(read('two-modules-stopped.txt'))
    # -fae still never builds a module that depends on a failed one.
    assert STOPPED.search(read('fail-at-end-dependent-skipped.txt'))
    for complete in ('two-modules-fail-at-end.txt', 'surefire3-fail.txt', 'surefire3-pass.txt'):
        assert not STOPPED.search(read(complete)), complete


def test_a_pom_is_discovered_as_the_test_command_and_its_wrapper_preferred(tmp_path, monkeypatch):
    from core import config
    (tmp_path / 'pom.xml').write_text('<project/>')
    assert config.discover_commands(tmp_path)['tests'] == 'mvn test'
    (tmp_path / 'mvnw').write_text('')
    (tmp_path / 'mvnw.cmd').write_text('')
    monkeypatch.setattr(config.os, 'name', 'nt')
    assert config.discover_commands(tmp_path)['tests'] == 'mvnw.cmd test'
    monkeypatch.setattr(config.os, 'name', 'posix')
    assert config.discover_commands(tmp_path)['tests'] == './mvnw test'
    # A wrapper for one platform only is used where it runs, and nowhere else.
    (tmp_path / 'mvnw.cmd').unlink()
    monkeypatch.setattr(config.os, 'name', 'nt')
    assert config.discover_commands(tmp_path)['tests'] == 'mvn test'


def test_the_review_asks_maven_to_build_every_module_it_can():
    from core.stress import _with_outcomes
    assert _with_outcomes('mvn test') == 'mvn -fae test'
    assert _with_outcomes('./mvnw -q verify 2>&1 | tail -20') == './mvnw -fae -q verify 2>&1 | tail -20'
    assert _with_outcomes('mvnw.cmd test') == 'mvnw.cmd -fae test'
    for chosen in ('mvn -fae test', 'mvn test --fail-at-end', 'mvn -ff test', 'mvn --fail-fast test',
                   'mvn -fn test', 'mvn --fail-never test'):
        assert _with_outcomes(chosen) == chosen


def test_a_compile_is_a_build_not_a_test_run(tmp_path):
    found = parsers.parse('mvn -q compile', '', 0, tmp_path)
    assert not any(r.kind in (Kind.SUITE, Kind.TEST) for r in found)


def test_the_wrapper_and_a_build_with_no_test_summary(tmp_path):
    _, suite = records(read('surefire3-pass.txt'), 0, tmp_path, './mvnw test')
    assert suite.counted and suite.passed == 1
    compile_error = '[ERROR] COMPILATION ERROR :\n[INFO] BUILD FAILURE\n'
    tests, suite = records(compile_error, 1, tmp_path)
    assert tests == [] and not suite.counted and suite.result is Result.FAIL
