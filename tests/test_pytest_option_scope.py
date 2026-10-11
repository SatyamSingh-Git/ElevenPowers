"""Options are not positional test identities; selectors still narrow a run."""
import subprocess
import sys

import pytest

from core.evidence import Kind, Result
from core.obligations import Obligation, SUITE_GREEN
from core.parsers import parse


def suite(root, command, output='2 passed in 0.01s', code=0):
    return next(row for row in parse(command, output, code, root) if row.kind is Kind.SUITE)


@pytest.mark.parametrize('options', [
    '-W ignore::UserWarning -q', '--pythonwarnings ignore::UserWarning -q',
    '--pythonwarnings=ignore::UserWarning -q', '-Wignore::UserWarning -q',
    '-o "filterwarnings=ignore::UserWarning" -q',
    '--override-ini="filterwarnings=ignore::UserWarning" -q',
    '-c "config/test_settings.ini" -q', '--rootdir "project/test_root.py" -q',
    '--junitxml reports/test_output.xml -q', '--tb short -q',
])
def test_option_values_cannot_scope_a_broad_run(tmp_path, options):
    command = 'python -m pytest ' + options
    row = suite(tmp_path, command)
    assert not Obligation._is_scoped(row), row.identity
    assert SUITE_GREEN.satisfied_by([row]) is row
    assert row.command == command and row.passed == 2


@pytest.mark.parametrize('options', [
    'tests/test_app.py::test_one -W ignore::UserWarning -q',
    '-W ignore::UserWarning "tests/test app.py::test_one" -q',
    '-W ignore::UserWarning tests/test_app.py tests -q',
    '-m "slow or integration" -q', '--deselect=tests/test_app.py::test_one -q',
    '-k "one or two" -q', '--last-failed -q',
])
def test_actual_targets_and_selectors_remain_scoped(tmp_path, options):
    row = suite(tmp_path, 'python -m pytest ' + options)
    assert Obligation._is_scoped(row)
    assert SUITE_GREEN.satisfied_by([row]) is None


def test_unknown_option_scope_stays_explicitly_unqualified(tmp_path):
    row = suite(tmp_path, 'python -m pytest --custom-selection something::else -q')
    assert row.coverage_issues
    assert 'pytest' in ' '.join(row.coverage_issues)


@pytest.mark.parametrize('node', [False, True])
def test_real_warning_filter_run_has_the_correct_scope_and_counts(tmp_path, node):
    (tmp_path / 'test_sample.py').write_text('def test_one(): assert True\ndef test_two(): assert True\n')
    args = [sys.executable, '-m', 'pytest', '-W', 'ignore::UserWarning', '-q']
    if node:
        args.append('test_sample.py::test_one')
    done = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True, timeout=15)
    assert done.returncode == 0
    command = 'python -m pytest -W ignore::UserWarning -q' + (' test_sample.py::test_one' if node else '')
    row = suite(tmp_path, command, done.stdout)
    assert row.result is Result.PASS and row.passed == (1 if node else 2)
    assert Obligation._is_scoped(row) is node


@pytest.mark.parametrize('options,scoped', [
    (['-qra'], False), (['-qk', 'one'], True),
    (['--debug', 'debug.py', '-q'], False), (['--debug=debug.py', '-q'], False),
    (['--sw-skip', '-q'], True), (['--stepwise-skip', '-q'], True),
])
def test_real_builtin_option_grammar_preserves_scope(tmp_path, options, scoped):
    (tmp_path / 'test_sample.py').write_text('def test_one(): assert True\ndef test_two(): assert True\n')
    cache = tmp_path / '.pytest_cache' / 'v' / 'cache'
    cache.mkdir(parents=True)
    (cache / 'stepwise').write_text('"test_sample.py::test_two"')
    done = subprocess.run([sys.executable, '-m', 'pytest', *options], cwd=tmp_path,
                          capture_output=True, text=True, timeout=15)
    assert done.returncode == 0, done.stdout + done.stderr
    row = suite(tmp_path, 'python -m pytest ' + ' '.join(options), done.stdout)
    assert not row.coverage_issues
    assert Obligation._is_scoped(row) is scoped
    assert (SUITE_GREEN.satisfied_by([row]) is None) is scoped
