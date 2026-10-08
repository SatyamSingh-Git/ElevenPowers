"""Literal invocation equivalence requires both a declared leaf and its root."""
import pytest

from core.config import Config, save
from core.evidence import Freshness, Kind, Result
from core.parsers import parse


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project with spaces'
    root.mkdir()
    (root / 'app.py').write_text('value = 1\n')
    save(root, Config(commands={'tests': 'npm run ci'}))
    return root


@pytest.mark.parametrize('prefix', ['cd . && ', 'cd "." && ', "cd '.' && ", 'absolute'])
@pytest.mark.parametrize('code,result', [(0, Result.PASS), (2, Result.FAIL), (None, Result.ERROR)])
def test_literal_wrapper_preserves_declaration_provenance_and_outcome(project, prefix, code, result):
    if prefix == 'absolute':
        prefix = f'cd "{project.as_posix()}" && '
    command = prefix + 'npm run ci'
    records = parse(command, 'checks complete', code, project)
    assert len(records) == 1
    row = records[0]
    assert row.kind is Kind.SUITE and row.result is result
    assert row.execution == ('incomplete' if code is None else 'complete')
    assert row.declaration == 'tests' and row.declared_command == 'npm run ci'
    assert row.command == command
    assert row.freshness(project) is Freshness.FRESH


@pytest.mark.parametrize('destination', ['missing', 'other'])
def test_wrong_or_missing_literal_directory_cannot_credit_project_tests(project, destination):
    if destination == 'other':
        (project / destination).mkdir()
    row = parse(f'cd {destination} && npm run ci', 'checks complete', 0, project)[0]
    assert row.execution == 'incomplete' and row.result is Result.ERROR
    assert row.coverage_issues


@pytest.mark.parametrize('command', [
    'cd . ; npm run ci', 'cd . || npm run ci', 'cd . && npm run ci || true',
    'cd . && npm run ci && echo done', 'cd . && npm run ci | cat',
    'cd . && npm run ci > saved.txt', 'cd . && npm run ci -- --focus',
    'cd . && cd . && npm run ci', 'cd "$PROJECT" && npm run ci',
    'cd `pwd` && npm run ci', 'cd $(pwd) && npm run ci',
    'cd ~ && npm run ci', 'cd * && npm run ci',
    'cd .\n && npm run ci', 'cd . && npm run ci\ntrue',
])
def test_unsupported_wrappers_are_not_declared_equivalences(project, command):
    assert not any(row.declaration for row in parse(command, '', 0, project))


def test_wrapped_counted_failure_overrides_zero_exit(project):
    row = parse('cd . && npm run ci', '# pass 2\n# fail 1\n', 0, project)[0]
    assert row.result is Result.FAIL and row.failed == 1


def test_exact_compound_declaration_remains_project_owned(project):
    command = 'cd tests && custom-check && other-check'
    save(project, Config(commands={'tests': command}))
    row = parse(command, 'checks complete', 0, project)[0]
    assert row.result is Result.PASS and row.declared_command == command


def test_wrapped_targeted_check_does_not_become_a_whole_suite(project):
    from core.obligations import SUITE_GREEN
    leaf = 'pytest tests/test_api.py -q'
    save(project, Config(commands={'tests': leaf}))
    row = parse('cd . && ' + leaf, '1 passed in 0.01s', 0, project)[0]
    assert row.declared_command == leaf
    assert not SUITE_GREEN.matches(row)
