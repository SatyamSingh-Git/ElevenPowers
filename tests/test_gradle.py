"""Gradle test runs: counted when Gradle counts, failing tests named (captured 2026-11-25).

Fixtures are real Gradle 8.10.2 output (JUnit 5.11.3, Java 17) with the build folder
replaced by C:/project.
"""
from pathlib import Path

from core import parsers
from core.evidence import Kind, Result

FIXTURES = Path(__file__).parent / 'fixtures' / 'gradle'


def read(name):
    return (FIXTURES / name).read_text(encoding='utf-8')


def records(output, exit_code, tmp_path, command='gradle test'):
    found = parsers.parse(command, output, exit_code, tmp_path)
    tests = sorted(r.identity for r in found if r.kind is Kind.TEST and r.result is Result.FAIL)
    suite = [r for r in found if r.kind is Kind.SUITE][-1]
    return tests, suite


def test_a_failing_run_is_counted_and_names_nested_and_parameterised_tests(tmp_path):
    tests, suite = records(read('fail.txt'), 1, tmp_path)
    assert tests == ['CalcTest.throwsOnPurpose', 'CalcTest.wrongOnPurpose', 'ShapesTest.Inner.deep',
                     'ShapesTest.positive(int).[2] 2']
    assert (suite.passed, suite.failed, suite.counted, suite.result) == (2, 4, True, Result.FAIL)


def test_the_count_outranks_an_exit_code_a_pipe_swallowed(tmp_path):
    _, suite = records(read('fail.txt'), 0, tmp_path, './gradlew test | tail -30')
    assert suite.result is Result.FAIL


def test_a_passing_run_prints_no_count_so_it_is_not_counted(tmp_path):
    for name in ('pass.txt', 'up-to-date.txt'):
        tests, suite = records(read(name), 0, tmp_path)
        assert (tests, suite.counted, suite.result) == ([], False, Result.PASS), name


def test_quiet_keeps_the_count_and_names_nothing(tmp_path):
    tests, suite = records(read('quiet-fail.txt'), 1, tmp_path, 'gradle test -q')
    assert tests == [] and (suite.passed, suite.failed, suite.counted) == (2, 4, True)


def test_two_failing_test_tasks_are_summed(tmp_path):
    tests, suite = records(read('multi-continue-two-failing.txt'), 1, tmp_path, 'gradle test --continue')
    assert (suite.passed, suite.failed) == (4, 4)
    assert len(tests) == 4


def test_a_build_task_that_is_not_a_test_run(tmp_path):
    found = parsers.parse('gradle compileJava', '', 0, tmp_path)
    assert not any(r.kind in (Kind.SUITE, Kind.TEST) for r in found)


def test_a_multi_project_build_that_failed_without_continue_may_have_stopped(tmp_path):
    from core.review import _stopped
    (tmp_path / 'settings.gradle').write_text("rootProject.name = 'p'\ninclude 'alpha', 'beta'\n")
    stopped = read('multi-stopped.txt')
    assert _stopped('gradle test', stopped, tmp_path)
    assert not _stopped('gradle test --continue', read('multi-continue-two-failing.txt'), tmp_path)
    # One failing task under --continue prints the same "Build failed" as a stopped build.
    one = read('multi-continue-one-failing.txt')
    assert 'FAILURE: Build failed' in one
    assert not _stopped('gradle test --continue', one, tmp_path)
    assert not _stopped('gradle test', read('pass.txt'), tmp_path)
    single = tmp_path / 'single'
    single.mkdir()
    (single / 'settings.gradle').write_text("rootProject.name = 'demo'\n")
    assert not _stopped('gradle test', read('fail.txt'), single)


def test_a_gradle_build_is_discovered_and_its_wrapper_preferred(tmp_path, monkeypatch):
    from core import config
    (tmp_path / 'build.gradle.kts').write_text('')
    assert config.discover_commands(tmp_path)['tests'] == 'gradle test'
    (tmp_path / 'gradlew').write_text('')
    (tmp_path / 'gradlew.bat').write_text('')
    monkeypatch.setattr(config.os, 'name', 'nt')
    assert config.discover_commands(tmp_path)['tests'] == 'gradlew.bat test'
    monkeypatch.setattr(config.os, 'name', 'posix')
    assert config.discover_commands(tmp_path)['tests'] == './gradlew test'
    (tmp_path / 'gradlew.bat').unlink()
    monkeypatch.setattr(config.os, 'name', 'nt')
    assert config.discover_commands(tmp_path)['tests'] == 'gradle test'
