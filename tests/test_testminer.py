"""TestMiner: behaviour that runs, but no test checks."""
import pytest

from core.testminer.functions import functions

SOURCE = '''\
def add(a, b):
    def inner():
        return 0
    return a + b


def log(x):
    """Print and return."""
    print(x)
    return x


class A:
    def size(self):
        return 1


class B:
    def size(self):
        return 2


def gen():
    yield 1


async def run():
    return 1


class Box:
    def __init__(self):
        self.n = 1


def one(): return 1


def doc():
    """Only a docstring."""


def outer():
    def g():
        yield 1
    return list(g())
'''


def test_functions_are_qualified_and_spans_cover_the_body():
    found = {f.name: f for f in functions(SOURCE)}
    assert set(found) == {'add', 'log', 'A.size', 'B.size', 'gen', 'run', 'Box.__init__', 'one', 'doc', 'outer'}
    assert (found['add'].first, found['add'].last) == (2, 4)
    assert (found['log'].first, found['log'].body, found['log'].last) == (8, 9, 10)
    assert found['A.size'].first == 15 and found['B.size'].first == 20


def test_bodies_that_cannot_be_emptied_say_why():
    found = {f.name: f.refused for f in functions(SOURCE)}
    assert found['gen'] == 'generator' and found['run'] == 'async function'
    assert found['Box.__init__'] == '__init__' and found['one'] == 'one-line function'
    assert found['doc'] == 'no statement besides a docstring'
    assert found['add'] == '' and found['log'] == '' and found['A.size'] == '' and found['outer'] == ''


def test_wrap_keeps_options_and_refuses_other_runners():
    from pathlib import Path
    from core.testminer.coverage_run import wrap
    assert wrap('python -m pytest -q tests', Path('rc'))[-4:] == ['-m', 'pytest', '-q', 'tests']
    assert wrap('python -m pytest -q', Path('rc'))[:6] == ['python', '-m', 'coverage', 'run', '--rcfile', 'rc']
    assert wrap('pytest -x', Path('rc'))[-3:] == ['-m', 'pytest', '-x']
    assert wrap('python -m unittest discover', Path('rc'))[-3:] == ['-m', 'unittest', 'discover']
    for bad in ('tox -e py', 'npm test', 'python -m pytest -n auto', 'pytest -p xdist', 'python -m pip install x'):
        with pytest.raises(ValueError, match='--command'):
            wrap(bad, Path('rc'))


def test_a_pytest_executable_runs_under_the_python_beside_it(tmp_path, monkeypatch):
    import os
    from pathlib import Path
    from core.testminer.coverage_run import wrap
    scripts = tmp_path / 'venv' / ('Scripts' if os.name == 'nt' else 'bin')
    scripts.mkdir(parents=True)
    suffix = '.exe' if os.name == 'nt' else ''
    (scripts / ('pytest' + suffix)).write_text('')
    (scripts / ('python' + suffix)).write_text('')
    assert wrap(f'"{scripts / "pytest"}" -q', Path('rc'))[0] == str(scripts / ('python' + suffix))
    monkeypatch.setenv('PATH', str(scripts))
    assert wrap('pytest -q', Path('rc'))[0] == str(scripts / ('python' + suffix))
    monkeypatch.setenv('PATH', str(tmp_path))
    assert wrap('pytest -q', Path('rc'))[0] == 'python'


def test_reached_reads_contexts_and_flags_fixture_only_lines():
    from core.testminer.coverage_run import reached
    from core.testminer.functions import Function
    # The real shape, from coverage.py 7.10.7 run on 2026-11-13.
    report = {'files': {'svc.py': {'contexts': {'2': ['tests.test_svc.T.test_add'], '6': [''], '7': [''],
                                                '9': ['', 'tests.test_svc.T.test_box']}}}}
    assert reached(report, 'svc.py', Function('add', 2, 2, 2, '')) == ({'tests.test_svc.T.test_add'}, False)
    assert reached(report, 'svc.py', Function('log', 6, 7, 6, '')) == (set(), True)
    assert reached(report, 'svc.py', Function('box', 9, 9, 9, '')) == ({'tests.test_svc.T.test_box'}, False)
    assert reached(report, 'svc.py', Function('never', 11, 12, 11, '')) == (set(), False)
    assert reached(report, 'other.py', Function('x', 1, 2, 1, '')) == (set(), False)


SERVICE = '''\
def add(a, b):
    total = a + b
    return total


def log(x):
    print(x)
    return x


def never(x):
    y = x * 2
    return y


def setup_only():
    value = 1
    return value


def one(): return 1
'''

SERVICE_TESTS = '''\
import pytest
from svc import add, log, setup_only


@pytest.fixture
def ready():
    return setup_only()


def test_add():
    assert add(1, 2) == 3


def test_log():
    log(5)


def test_uses_fixture(ready):
    assert True
'''


def service(root, tests=SERVICE_TESTS):
    import subprocess
    root.mkdir(parents=True, exist_ok=True)
    (root / 'svc.py').write_text(SERVICE)
    (root / 'tests').mkdir(exist_ok=True)
    (root / 'tests/test_svc.py').write_text(tests)
    (root / 'pytest.ini').write_text('[pytest]\npythonpath = .\n')
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=root, check=True)
    subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'base'], cwd=root, check=True)
    return root


# The fixture's tests run under the interpreter running this suite; CI installs coverage.py 7.10.7.
needs_coverage = pytest.mark.skipif(__import__('importlib.util').util.find_spec('coverage') is None,
                                    reason='coverage.py is not installed for this interpreter')


def pytest_command():
    import sys
    return f'"{sys.executable}" -m pytest -q -p no:cacheprovider'


def verdicts(result):
    return {f['name']: f['verdict'] for f in result['functions']}


@needs_coverage
def test_fixture_service_gets_each_verdict(tmp_path):
    from core.testminer.runner import mine
    root = service(tmp_path)
    result = mine(root, paths=('svc.py',), command=pytest_command())
    assert verdicts(result) == {'add': 'checked', 'log': 'reached, not checked', 'never': 'not reached',
                                'setup_only': 'unknown', 'one': 'unknown'}
    reasons = {f['name']: f['reason'] for f in result['functions']}
    assert 'outside any test' in reasons['setup_only'] and reasons['one'] == 'one-line function'
    log = next(f for f in result['functions'] if f['name'] == 'log')
    assert log['tests'] == ['test_svc.test_log']
    assert (root / 'svc.py').read_text() == SERVICE
    assert (root / '.elevenpowers/testminer.json').exists()


@needs_coverage
def test_verdicts_flip_both_ways(tmp_path):
    from core.testminer.runner import mine
    asserted = SERVICE_TESTS.replace('    log(5)\n', '    assert log(5) == 5\n')
    no_add = SERVICE_TESTS.replace('def test_add():\n    assert add(1, 2) == 3\n', '')
    first = verdicts(mine(service(tmp_path / 'a', asserted), paths=('svc.py',), command=pytest_command()))
    second = verdicts(mine(service(tmp_path / 'b', no_add), paths=('svc.py',), command=pytest_command()))
    assert first['log'] == 'checked' and second['add'] == 'not reached'


@needs_coverage
def test_unittest_names_are_run_as_given(tmp_path):
    import sys
    from core.testminer.runner import mine
    tests = ('import unittest\nfrom svc import add, log\n\n\nclass T(unittest.TestCase):\n'
             '    def test_add(self):\n        self.assertEqual(add(1, 2), 3)\n\n'
             '    def test_log(self):\n        log(5)\n')
    root = service(tmp_path, tests)
    (root / 'tests/__init__.py').write_text('')
    result = mine(root, names=('svc.py::add', 'svc.py::log'), command=f'"{sys.executable}" -m unittest')
    assert verdicts(result) == {'add': 'checked', 'log': 'reached, not checked'}


@needs_coverage
def test_red_baseline_and_missing_coverage_are_unknown(tmp_path):
    import shutil
    import subprocess
    from core.testminer.runner import mine
    red = mine(service(tmp_path / 'red', SERVICE_TESTS + '\n\ndef test_red():\n    assert False\n'),
               paths=('svc.py',), command=pytest_command())
    assert set(verdicts(red).values()) == {'unknown'} and 'baseline' in red['issues'][0]
    launcher = shutil.which('py')
    if launcher is None or subprocess.run([launcher, '-3.11', '-c', 'import coverage'], capture_output=True).returncode == 0:
        pytest.skip('needs a Python without coverage.py')
    python = subprocess.run([launcher, '-3.11', '-c', 'import sys; print(sys.executable)'],
                            capture_output=True, text=True).stdout.strip()
    plain = mine(service(tmp_path / 'plain'), paths=('svc.py',), command=f'"{python}" -m pytest -q')
    assert set(verdicts(plain).values()) == {'unknown'} and 'pip install coverage' in plain['issues'][0]


def test_nothing_selected_and_other_runners_are_refused(tmp_path):
    from core.testminer.runner import mine
    root = service(tmp_path)
    with pytest.raises(ValueError, match='--base'):
        mine(root, command=pytest_command())
    with pytest.raises(ValueError, match='--command'):
        mine(root, paths=('svc.py',), command='tox -e py')


@needs_coverage
def test_unmapped_selection_falls_back_to_the_whole_command(tmp_path, monkeypatch):
    from core.testminer import runner
    monkeypatch.setattr(runner, 'node', lambda root, files, context: 'tests/test_svc.py::does_not_exist')
    result = runner.mine(service(tmp_path), names=('svc.py::log', 'svc.py::add'), command=pytest_command())
    assert verdicts(result) == {'log': 'reached, not checked', 'add': 'checked'}


@needs_coverage
def test_cli_prints_verdicts_and_json(tmp_path):
    import json
    import subprocess
    import sys
    from pathlib import Path
    root = service(tmp_path)
    cli = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_testminer.py'
    done = subprocess.run([sys.executable, str(cli), '--project', str(root), '--path', 'svc.py',
                           '--command', pytest_command(), '--json'], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert {f['name'] for f in json.loads(done.stdout)['functions']} == {'add', 'log', 'never', 'setup_only', 'one'}
    text = subprocess.run([sys.executable, str(cli), '--project', str(root), '--path', 'svc.py',
                           '--command', pytest_command()], capture_output=True, text=True).stdout
    assert 'svc.py:7 log: reached, not checked (test_svc.test_log)' in text
    assert 'add: checked' not in text and '1 function checked by its tests (--all lists them)' in text
    listed = subprocess.run([sys.executable, str(cli), '--project', str(root), '--path', 'svc.py', '--all',
                             '--command', pytest_command()], capture_output=True, text=True).stdout
    assert 'svc.py:2 add: checked' in listed
    capped = subprocess.run([sys.executable, str(cli), '--project', str(root), '--path', 'svc.py', '--limit', '2',
                             '--command', pytest_command()], capture_output=True, text=True).stdout
    assert '3 more functions not examined (budget)' in capped and 'never' not in capped
    refused = subprocess.run([sys.executable, str(cli), '--project', str(root)], capture_output=True, text=True)
    assert refused.returncode == 2 and '--base' in refused.stderr


def test_coverage_missing_in_the_test_interpreter_is_unknown_everywhere(tmp_path, monkeypatch):
    from core.strength.execution import Execution
    from core.testminer import runner
    real = runner.execute

    def without_coverage(argv, *args, **kwargs):
        if 'import coverage; print(coverage.version_info[0])' in argv:
            return Execution('complete', 1, '', "ModuleNotFoundError: No module named 'coverage'")
        return real(argv, *args, **kwargs)
    monkeypatch.setattr(runner, 'execute', without_coverage)
    result = runner.mine(service(tmp_path), paths=('svc.py',), command=pytest_command())
    assert set(verdicts(result).values()) == {'unknown'}
    assert result['issues'] == [runner.INSTALL] and 'pip install coverage' in runner.INSTALL


@needs_coverage
def test_over_the_limit_is_budget_and_a_hanging_mutant_is_checked(tmp_path):
    from core.testminer.runner import mine
    root = service(tmp_path, SERVICE_TESTS + '\n\nfrom svc import done_yet\n\n\ndef test_waits():\n'
                                             '    while not done_yet():\n        pass\n')
    (root / 'svc.py').write_text('def done_yet():\n    flag = True\n    return flag\n\n\n' + SERVICE)
    import subprocess
    subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qam', 'done_yet'], cwd=root, check=True)
    result = mine(root, names=('svc.py::done_yet', 'svc.py::add', 'svc.py::log'), command=pytest_command(),
                  limit=2, test_seconds=8)
    got = {f['name']: (f['verdict'], f['reason']) for f in result['functions']}
    assert got['done_yet'] == ('checked', 'timed out') and got['add'][0] == 'checked'
    assert got['log'] == ('unknown', 'budget')


@pytest.mark.parametrize('code, output, expected', [
    # Printed by pytest 9.1.1 for a node id that does not exist (exit 4), 2026-11-13.
    (4, 'ERROR: not found: C:\\p\\tests\\test_svc.py::T::nope\n(no match in any of [<UnitTestCase T>])\n\n',
     ('unknown', 'the selected tests did not run')),
    (5, '\nno tests ran in 0.01s\n', ('unknown', 'the selected tests did not run')),
    # The fixture debugging run above: a setup error beside passing tests.
    (1, '..E.\n3 passed, 1 error in 0.01s\n', ('checked', '')),
    (0, '...\n3 passed in 0.04s\n', ('reached, not checked', '')),
    # pytest's internal-error exit: nothing failed, yet the run did not end cleanly.
    (3, '...\n3 passed in 0.04s\n', ('unknown', 'the selected tests did not run')),
])
def test_mutant_outcomes(tmp_path, code, output, expected):
    import time
    from core.strength.execution import Execution
    from core.testminer.runner import _verdict
    argv = ['python', '-m', 'pytest', '-q']
    assert _verdict(Execution('complete', code, output, ''), argv, tmp_path, time.monotonic() + 60) == expected


# Found by the final review, 2026-11-13.

def test_stub_bodies_and_a_body_on_the_signature_line_are_refused():
    source = ('class A:\n    def stub(self):\n        ...\n\n    def nothing(self):\n        """Doc."""\n        pass\n\n'
              'def wide(a,\n         b): return a + b\n')
    found = {f.name: f.refused for f in functions(source)}
    assert found['A.stub'] == 'body is only pass or ...'
    assert found['A.nothing'] == 'body is only pass or ...'
    assert found['wide'] == 'one-line function'


def test_a_getter_and_its_setter_are_both_kept():
    source = ('class P:\n    @property\n    def size(self):\n        return self._s\n\n'
              '    @size.setter\n    def size(self, v):\n        self._s = v\n')
    assert [(f.name, f.first) for f in functions(source)] == [('P.size', 4), ('P.size', 8)]


@needs_coverage
def test_any_spelling_of_the_path_gives_the_same_verdicts(tmp_path):
    import os
    from core.testminer.runner import mine
    root = service(tmp_path)
    plain = verdicts(mine(root, paths=('svc.py',), command=pytest_command()))
    for spelling in ('./svc.py', '.' + os.sep + 'svc.py', str(root / 'svc.py')):
        assert verdicts(mine(root, paths=(spelling,), command=pytest_command())) == plain, spelling
    assert verdicts(mine(root, names=('./svc.py::log',), command=pytest_command())) == {'log': 'reached, not checked'}
    with pytest.raises(ValueError, match='outside the project'):
        mine(root, paths=(str(tmp_path.parent / 'elsewhere.py'),), command=pytest_command())


@needs_coverage
def test_both_definitions_of_one_name_get_a_verdict(tmp_path):
    from core.testminer.runner import mine
    root = service(tmp_path)
    (root / 'box.py').write_text('class P:\n    @property\n    def size(self):\n        return self._s\n\n'
                                 '    @size.setter\n    def size(self, v):\n        self._s = v\n')
    result = mine(root, paths=('box.py',), command=pytest_command())
    assert [(f['name'], f['line']) for f in result['functions']] == [('P.size', 4), ('P.size', 8)]


@needs_coverage
def test_a_file_no_test_imported_from_the_copy_is_unknown(tmp_path):
    from core.testminer.runner import mine
    root = service(tmp_path)
    (root / 'orphan.py').write_text('def lonely(x):\n    y = x + 1\n    return y\n')
    import subprocess
    subprocess.run(['git', 'add', '-A'], cwd=root, check=True)
    result = mine(root, paths=('orphan.py',), command=pytest_command())
    assert [(f['verdict'], f['reason']) for f in result['functions']] == [
        ('unknown', 'no line of this file ran under the tests: never imported by them, or imported from an installed copy')]


@needs_coverage
def test_base_selects_the_changed_functions_by_ref_name(tmp_path):
    import subprocess
    from core.testminer.runner import mine
    root = service(tmp_path)
    subprocess.run(['git', 'branch', 'start'], cwd=root, check=True)
    (root / 'svc.py').write_text(SERVICE.replace('    print(x)\n', '    print(x, end="")\n'))
    result = mine(root, base='start', command=pytest_command())
    assert verdicts(result) == {'log': 'reached, not checked'}


def test_base_selects_a_signature_or_decorator_change_and_a_deleted_line(tmp_path):
    import subprocess
    import time
    from core.testminer.runner import _selected
    source = ('import functools\n\n\n@functools.cache\ndef cached(x):\n    y = x * 2\n    return y\n\n\n'
              'def scaled(x, k=2):\n    y = x * k\n    return y\n\n\n'
              'def trimmed(x):\n    x = x + 1\n    x = x * 2\n    return x\n\n\ndef untouched(x):\n    return x\n')
    (tmp_path / 'm.py').write_text(source)
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=tmp_path, check=True)
    subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'base'], cwd=tmp_path, check=True)
    (tmp_path / 'm.py').write_text(source.replace('@functools.cache', '@functools.lru_cache')
                                   .replace('def scaled(x, k=2):', 'def scaled(x, k=3):').replace('    x = x * 2\n', ''))
    chosen = _selected(tmp_path, 'HEAD', (), (), time.monotonic() + 30)
    assert [fn.name for _, fn in chosen] == ['cached', 'scaled', 'trimmed']


def test_a_file_python_cannot_parse_is_refused_by_name(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    from core.testminer.runner import mine
    (tmp_path / 'bad.py').write_text('def broken(:\n    return 1\n')
    with pytest.raises(ValueError, match=r'bad\.py: Python cannot parse it'):
        mine(tmp_path, paths=('bad.py',), command='python -m pytest')
    cli = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_testminer.py'
    done = subprocess.run([sys.executable, str(cli), '--project', str(tmp_path), '--path', 'bad.py',
                           '--command', 'python -m pytest'], capture_output=True, text=True)
    assert done.returncode == 2 and 'Traceback' not in done.stderr and 'bad.py' in done.stderr


def test_base_refuses_a_project_below_its_repository_root(tmp_path):
    import subprocess
    from core.testminer.runner import mine
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    (tmp_path / 'pkg').mkdir()
    (tmp_path / 'pkg/svc.py').write_text(SERVICE)
    subprocess.run(['git', 'add', '-A'], cwd=tmp_path, check=True)
    subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'base'], cwd=tmp_path, check=True)
    with pytest.raises(ValueError, match='repository root'):
        mine(tmp_path / 'pkg', base='HEAD', command=pytest_command())
    with pytest.raises(ValueError, match='not a commit'):
        mine(tmp_path, base='no-such-ref', command=pytest_command())
