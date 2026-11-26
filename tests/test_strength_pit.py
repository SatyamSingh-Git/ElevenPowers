"""PIT for changed Java lines (captured 2026-11-26).

tests/fixtures/pit/mixed.xml is PIT 1.30.2's report for the sources below, from Maven 3.9.9;
Gradle 8.10.2 with gradle-pitest-plugin 1.19.0 wrote the same bytes.
"""
import shutil
import time
from pathlib import Path

from core.strength import pit
from core.strength.execution import Budget, Execution

REPORT = Path(__file__).parent / 'fixtures' / 'pit' / 'mixed.xml'
SHAPES = 'src/main/java/demo/Shapes.java'
A_UTIL = 'src/main/java/a/Util.java'
B_UTIL = 'src/main/java/b/Util.java'
SOURCES = {
    SHAPES: 'package demo;\n\npublic class Shapes {\n    public static boolean big(int n) {\n        return n > 10;\n'
            '    }\n\n    public static int unused(int n) {\n        return n + 1;\n    }\n\n'
            '    public static class Inner {\n        public int twice(int n) {\n            return n * 2;\n'
            '        }\n    }\n}\n',
    A_UTIL: 'package a;\n\npublic class Util {\n    public static int one() {\n        return 1;\n    }\n}\n',
    B_UTIL: 'package b;\n\npublic class Util {\n    public static int two() {\n        return 2;\n    }\n}\n',
}


def project(root):
    for path, text in SOURCES.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text)
    return root


def written(root, where='target/pit-reports'):
    (root / where).mkdir(parents=True, exist_ok=True)
    shutil.copy(REPORT, root / where / 'mutations.xml')


def seen(found):
    return [(o.path, o.line, o.status, o.operator, o.context) for o in found]


def test_the_tool_is_the_one_the_tests_use():
    assert pit.tool('./gradlew test | tail') == './gradlew'
    assert pit.tool('cd x && mvnw.cmd -q test') == 'mvnw.cmd'
    assert pit.tool('mvn -fae verify') == 'mvn'
    assert pit.tool('make test') is None
    assert pit.tool('cd gradle && npm test') is None


def test_targets_cover_nested_classes_and_the_default_package(tmp_path):
    project(tmp_path)
    (tmp_path / 'Bare.java').write_text('public class Bare {}\n')
    assert pit.targets(tmp_path, [SHAPES, A_UTIL, 'Bare.java', SHAPES]) == ['Bare*', 'a.Util*', 'demo.Shapes*']


def test_maven_invocation_carries_the_junit5_plugin_and_never_fails_on_no_mutations(tmp_path):
    assert pit.invocation('mvnw.cmd', ['a.Util*', 'demo.Shapes*'], tmp_path) == [
        '-B', 'dependency:copy', '-Dartifact=org.pitest:pitest-junit5-plugin:1.2.3', f'-DoutputDirectory={tmp_path}',
        'test-compile', 'org.pitest:pitest-maven:1.30.2:mutationCoverage', '-DtargetClasses=a.Util*,demo.Shapes*',
        '-DoutputFormats=XML', '-DtimestampedReports=false', '-DfailWhenNoMutations=false',
        f"-DadditionalClasspathElements={tmp_path / 'pitest-junit5-plugin-1.2.3.jar'}"]


def test_gradle_invocation_applies_the_plugin_per_project(tmp_path):
    assert pit.invocation('./gradlew', ['demo.Shapes*'], tmp_path) == [
        '--init-script', str(tmp_path / 'pit.gradle'), '--continue', 'pitest', '-PepPitTargets=demo.Shapes*']
    script = (tmp_path / 'pit.gradle').read_text()
    for needed in ('project.pluginManager.apply', "gradle-pitest-plugin:1.19.0'", "'1.30.2'", "'1.2.3'", 'epPitTargets',
                   'failWhenNoMutations = false', 'timestampedReports = false'):
        assert needed in script, needed


def test_reports_map_to_changed_lines_with_pit_statuses(tmp_path):
    project(tmp_path)
    written(tmp_path)
    found = pit.observations(tmp_path, [SHAPES], {SHAPES: [[5, 5], [9, 9]]})
    assert seen(found) == [
        (SHAPES, 5, 'undetected', 'changed conditional boundary', 'Shapes.big'),
        (SHAPES, 5, 'detected', 'negated conditional', 'Shapes.big'),
        (SHAPES, 5, 'detected', 'replaced boolean return with true for demo/Shapes::big', 'Shapes.big'),
        (SHAPES, 9, 'undetected', 'Replaced integer addition with subtraction', 'Shapes.unused'),
        (SHAPES, 9, 'undetected', 'replaced int return with 0 for demo/Shapes::unused', 'Shapes.unused')]
    assert len({o.id for o in found}) == 5
    assert all(o.relevance == 'changed_lines' for o in found)
    nested = pit.observations(tmp_path, [SHAPES], {SHAPES: [[14, 14]]})
    assert [o.context for o in nested] == ['Shapes.Inner.twice'] * 2


def test_same_file_name_in_two_packages(tmp_path):
    project(tmp_path)
    written(tmp_path, 'beta/build/reports/pitest')
    found = pit.observations(tmp_path, [A_UTIL, B_UTIL], {A_UTIL: [], B_UTIL: [[5, 5]]})
    assert seen(found) == [(B_UTIL, 5, 'detected', 'replaced int return with 0 for b/Util::two', 'Util.two')]
    found = pit.observations(tmp_path, [A_UTIL, B_UTIL], {A_UTIL: [[5, 5]], B_UTIL: []})
    assert seen(found) == [(A_UTIL, 5, 'detected', 'replaced int return with 0 for a/Util::one', 'Util.one')]


def test_a_timed_out_mutant_is_detected_and_an_unknown_status_is_an_error(tmp_path):
    path = 'src/main/java/loop/Sum.java'
    (tmp_path / path).parent.mkdir(parents=True)
    (tmp_path / path).write_text('package loop;\n\npublic class Sum {\n' + '\n' * 10)
    report = tmp_path / 'target/pit-reports/mutations.xml'
    report.parent.mkdir(parents=True)
    timed_out = (REPORT.parent / 'timed-out.xml').read_text(encoding='utf-8')
    report.write_text(timed_out, encoding='utf-8')
    assert seen(pit.observations(tmp_path, [path], {path: [[9, 9]]})) == [
        (path, 9, 'detected', 'Replaced long addition with subtraction', 'Sum.upTo')]
    # PIT writes this report out of line order (7, 8, 9, 7, 11).
    assert [o.line for o in pit.observations(tmp_path, [path], {path: [[7, 11]]})] == [7, 7, 8, 9, 11]
    # The other statuses PIT's own summary names, on the same record.
    for status, expected in (('MEMORY_ERROR', 'detected'), ('NON_VIABLE', 'invalid'), ('NOT_STARTED', 'not_run'),
                             ('STARTED', 'not_run'), ('RUN_ERROR', 'error'), ('SURVIVED', 'undetected')):
        report.write_text(timed_out.replace("status='TIMED_OUT'", f"status='{status}'"), encoding='utf-8')
        assert [o.status for o in pit.observations(tmp_path, [path], {path: [[9, 9]]})] == [expected], status


def test_only_pit_report_folders_are_read_or_cleared(tmp_path, monkeypatch):
    project(tmp_path)
    written(tmp_path, 'src/test/resources')
    assert pit.observations(tmp_path, [SHAPES], {SHAPES: [[5, 5]]}) == []
    monkeypatch.setattr(pit.shutil, 'which', lambda name: '/bin/' + name)
    stub(monkeypatch, Execution('complete', 0))
    pit.run(tmp_path, [SHAPES], {SHAPES: [[5, 5]]}, 'mvn test', budget(), 8)
    assert (tmp_path / 'src/test/resources/mutations.xml').is_file()


def test_the_reason_is_the_build_tools_own_first_error_line():
    maven = ('[INFO] BUILD FAILURE\n[ERROR] Failed to execute goal org.pitest:pitest-maven:1.30.2:mutationCoverage\n'
             '[ERROR] See https://pitest.org for more details.\n[ERROR] -> [Help 1]\n')
    assert pit._reason(maven) == '[ERROR] Failed to execute goal org.pitest:pitest-maven:1.30.2:mutationCoverage'
    gradle = (Path(__file__).parent / 'fixtures' / 'gradle' / 'fail.txt').read_text(encoding='utf-8')
    assert pit._reason(gradle) == "Execution failed for task ':test'."


def stub(monkeypatch, done, write=None):
    calls = []

    def execute(command, root, budget, seconds, *, shell=True, original=None):
        calls.append(command)
        if write:
            written(root)
        return done
    monkeypatch.setattr(pit, 'execute', execute)
    return calls


def budget():
    return Budget(time.monotonic() + 60, 8)


def test_a_stale_report_is_not_read(tmp_path, monkeypatch):
    project(tmp_path)
    (tmp_path / 'mvnw').write_text('')
    written(tmp_path)
    calls = stub(monkeypatch, Execution('complete', 0))
    found, issues, more = pit.run(tmp_path, [SHAPES], {SHAPES: [[5, 5]]}, './mvnw test', budget(), 8)
    assert (found, more) == ([], False) and calls
    assert calls[0][0] == str(tmp_path / 'mvnw')
    assert issues == ['PIT did not complete (it wrote no report)']
    calls = stub(monkeypatch, Execution('complete', 0), write=True)
    found, issues, more = pit.run(tmp_path, [SHAPES], {SHAPES: [[5, 5]]}, './mvnw test', budget(), 8)
    assert len(found) == 3 and issues == []


def test_the_limit_keeps_the_first_mutants_and_says_more(tmp_path, monkeypatch):
    project(tmp_path)
    stub(monkeypatch, Execution('complete', 0), write=True)
    monkeypatch.setattr(pit.shutil, 'which', lambda name: '/bin/' + name)
    found, issues, more = pit.run(tmp_path, [SHAPES], {SHAPES: [[5, 5]]}, 'mvn test', budget(), 1)
    assert seen(found) == [(SHAPES, 5, 'undetected', 'changed conditional boundary', 'Shapes.big')] and more


def test_a_run_that_failed_or_ran_out_of_time_is_an_issue(tmp_path, monkeypatch):
    project(tmp_path)
    monkeypatch.setattr(pit.shutil, 'which', lambda name: '/bin/' + name)
    stub(monkeypatch, Execution('complete', 1, 'x\n[ERROR] BUILD FAILURE\n', ''))
    assert pit.run(tmp_path, [SHAPES], {SHAPES: [[5, 5]]}, 'mvn test', budget(), 8)[1] == [
        'PIT did not complete (exit 1: [ERROR] BUILD FAILURE)']
    stub(monkeypatch, Execution('timed_out'), write=True)
    assert pit.run(tmp_path, [SHAPES], {SHAPES: [[5, 5]]}, 'mvn test', budget(), 8)[:2] == (
        [], ['PIT did not complete (timed out)'])
    monkeypatch.setattr(pit.shutil, 'which', lambda name: None)
    assert pit.run(tmp_path, [SHAPES], {SHAPES: [[5, 5]]}, 'mvn test', budget(), 8)[1] == [
        'PIT needs mvn, which was not found']


def java_repository(root):
    from tests.test_strength import repository
    base = repository(root)
    project(root)
    (root / 'src/test/java/demo').mkdir(parents=True)
    (root / 'src/test/java/demo/ShapesTest.java').write_text('package demo;\n')
    return base


def java_ledger(root, command, monkeypatch):
    from core.config import Config
    from core.ledger import Ledger
    from core.strength import runner
    from core.strength.baseline import Baseline
    monkeypatch.setattr(runner, 'baseline', lambda *args: Baseline('passed', passed=1))
    ledger = Ledger(root=root, task='t', base=java_repository(root))
    ledger._config = Config(commands={'tests': command}, strength={'max_mutants': 4})
    return ledger


def test_a_changed_java_file_is_selected_and_its_test_is_not(tmp_path):
    from core.strength.scope import select
    base = java_repository(tmp_path)
    assert select(tmp_path, base, time.monotonic() + 10).paths == [A_UTIL, B_UTIL, SHAPES]


def test_java_needs_a_maven_or_gradle_command(tmp_path, monkeypatch):
    from core.strength.runner import analyze
    value = analyze(java_ledger(tmp_path, 'make test', monkeypatch))
    assert value['state'] == 'unavailable'
    assert 'Java mutation needs a Maven or Gradle test command; "make test" is neither' in value['issues']


def test_pit_observations_enter_the_record(tmp_path, monkeypatch):
    from core.strength.model import Observation
    from core.strength.runner import analyze
    asked = []

    def run(root, paths, regions, command, budget, maximum):
        asked.append((root != tmp_path, paths, regions, command, maximum))
        return [Observation(f'pit:{n}', SHAPES, 5, 'negated conditional', status, relevance='changed_lines',
                            context='Shapes.big') for n, status in enumerate(('detected', 'undetected'))], [], False
    monkeypatch.setattr(pit, 'run', run)
    value = analyze(java_ledger(tmp_path, 'mvn test', monkeypatch))
    assert asked == [(True, [A_UTIL, B_UTIL, SHAPES], {A_UTIL: [[1, 7]], B_UTIL: [[1, 7]], SHAPES: [[1, 17]]},
                      'mvn test', 4)]
    assert value['engine_versions'] == {'pit': '1.30.2'} and value['attempts'] == 2
    assert [o['status'] for o in value['observations']] == ['detected', 'undetected']
    assert pit.LIMITATION in value['limitations'] and value['state'] == 'complete', value['issues']


def test_pit_that_did_not_complete_leaves_the_record_incomplete(tmp_path, monkeypatch):
    from core.strength.runner import analyze
    monkeypatch.setattr(pit, 'run', lambda *args: ([], ['PIT did not complete (exit 1: [ERROR] x)'], False))
    value = analyze(java_ledger(tmp_path, './gradlew test', monkeypatch))
    assert value['state'] == 'incomplete' and 'PIT did not complete (exit 1: [ERROR] x)' in value['issues']


def test_an_unchanged_java_change_reuses_its_pit_record(tmp_path, monkeypatch):
    from core.strength.model import Observation
    from core.strength.runner import analyze
    runs = []

    def run(*args):
        runs.append(args)
        return [Observation('pit:0', SHAPES, 5, 'negated conditional', 'detected', relevance='changed_lines',
                            context='Shapes.big')], [], False
    monkeypatch.setattr(pit, 'run', run)
    ledger = java_ledger(tmp_path, 'mvn test', monkeypatch)
    first = analyze(ledger)
    assert analyze(ledger)['observations'] == first['observations'] and len(runs) == 1
    monkeypatch.setattr(pit, 'PIT', '1.30.3')
    analyze(ledger)
    assert len(runs) == 2


def test_the_review_keeps_pit_descriptions_whole_and_says_pit_ran_its_own_tests(tmp_path, monkeypatch):
    from core import review
    from core.strength import runner
    record = {'state': 'complete', 'issues': [], 'summary': {}, 'attempts': 2,
              'settings': {'max_mutants': 8, 'seconds': 60}, 'limitations': [pit.LIMITATION],
              'observations': [
                  {'id': 'pit:x', 'path': SHAPES, 'line': 5, 'end_line': 5, 'context': 'Shapes.big',
                   'status': 'undetected', 'operator': 'replaced boolean return with true for demo/Shapes::big'},
                  {'id': 'cr:y', 'path': 'a.py', 'line': 1, 'end_line': 1, 'context': 'f',
                   'status': 'undetected', 'operator': 'core/NumberReplacer'}]}
    monkeypatch.setattr(runner, 'analyze', lambda *args, **kwargs: record)
    strength = review._strength(tmp_path, tmp_path, 'base', 'mvn test', {})
    assert [item['operators'] for item in strength['unpinned']] == [
        ['NumberReplacer'], ['replaced boolean return with true for demo/Shapes::big']]
    report = {'command': 'mvn test', 'kept': [], 'strength': strength, 'functions': None}
    assert f'Mutation analysis: {pit.LIMITATION}' in review._limits(report)
    record['limitations'] = []
    assert not any(pit.LIMITATION in line for line in review._limits(
        {**report, 'strength': review._strength(tmp_path, tmp_path, 'base', 'mvn test', {})}))
