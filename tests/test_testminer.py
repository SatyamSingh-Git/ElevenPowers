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


@pytest.mark.parametrize('name, text', [
    ('pytest.ini', '[pytest]\naddopts = -q -n auto\n'),
    ('pyproject.toml', '[tool.pytest.ini_options]\naddopts = ["-n", "4"]\n'),
    ('tox.ini', '[pytest]\naddopts = --numprocesses=auto\n'),
    ('setup.cfg', '[tool:pytest]\naddopts = -p xdist -n2\n'),
])
def test_parallel_workers_from_the_project_config_are_refused_and_n0_is_the_way_out(tmp_path, name, text):
    from pathlib import Path
    from core.testminer.coverage_run import wrap
    (tmp_path / name).write_text(text)
    with pytest.raises(ValueError, match='-n 0'):
        wrap('python -m pytest -q', Path('rc'), tmp_path)
    assert wrap('python -m pytest -q -n 0', Path('rc'), tmp_path)[-3:] == ['-q', '-n', '0']
    assert wrap('python -m pytest -q', Path('rc'), tmp_path.parent / 'elsewhere')[-1] == '-q'


def test_quoted_options_lose_their_quotes_on_every_platform():
    from pathlib import Path
    from core.testminer.coverage_run import wrap
    assert wrap("python -m pytest -k 'a or b' -q", Path('rc'))[-3:] == ['-k', 'a or b', '-q']
    assert wrap('python -m pytest -k "a or b"', Path('rc'))[-2:] == ['-k', 'a or b']


def test_a_pytest_executable_runs_under_the_python_beside_it(tmp_path, monkeypatch):
    import os
    from pathlib import Path
    from core.testminer.coverage_run import wrap
    scripts = tmp_path / 'venv' / ('Scripts' if os.name == 'nt' else 'bin')
    scripts.mkdir(parents=True)
    suffix = '.exe' if os.name == 'nt' else ''
    for name in ('pytest', 'python'):
        (scripts / (name + suffix)).write_text('')
        # shutil.which on POSIX finds only executable files, as installed scripts are.
        (scripts / (name + suffix)).chmod(0o755)
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
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    with pytest.raises(ValueError, match=r'bad\.py: Python cannot parse it'):
        mine(tmp_path, paths=('bad.py',), command='python -m pytest')
    cli = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_testminer.py'
    done = subprocess.run([sys.executable, str(cli), '--project', str(tmp_path), '--path', 'bad.py',
                           '--command', 'python -m pytest'], capture_output=True, text=True)
    assert done.returncode == 2 and 'Traceback' not in done.stderr and 'bad.py' in done.stderr


def test_a_deadline_while_copying_is_the_budget(tmp_path, monkeypatch):
    from core.testminer import runner

    def slow(*args, **kwargs):
        raise TimeoutError('strength deadline reached copying inputs')
    monkeypatch.setattr(runner, 'snapshot', slow)
    result = runner.mine(service(tmp_path), paths=('svc.py',), command='python -m pytest')
    assert {(f['verdict'], f['reason']) for f in result['functions']} == {('unknown', 'budget')}
    assert result['issues'] == ['the time budget ran out; raise --seconds']


def test_a_project_outside_git_is_refused_with_the_reason(tmp_path):
    from core.testminer.runner import mine
    (tmp_path / 'svc.py').write_text(SERVICE)
    for selection in ({'paths': ('svc.py',)}, {'base': 'HEAD'}):
        with pytest.raises(ValueError, match='not a Git repository'):
            mine(tmp_path, command='python -m pytest', **selection)


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


# Slice 2: more than one extreme value.

@pytest.mark.parametrize('code, values', [
    ('def f() -> bool:\n    x = 1\n    return x\n', ('None', 'True', 'False')),
    ('def f() -> int:\n    x = 1\n    return x\n', ('None', '0', '1')),
    ('def f() -> float:\n    x = 1\n    return x\n', ('None', '0.0', '1.0')),
    ('def f() -> str:\n    x = 1\n    return x\n', ('None', "''", "'A'")),
    ('def f() -> bytes:\n    x = 1\n    return x\n', ('None', "b''", "b'A'")),
    ('def f() -> list[int]:\n    x = 1\n    return x\n', ('None', '[]', '[None]')),
    ('def f() -> typing.Dict[str, int]:\n    x = 1\n    return x\n', ('None', '{}', '{None: None}')),
    ('def f() -> set:\n    x = 1\n    return x\n', ('None', 'set()', '{None}')),
    ('def f() -> tuple:\n    x = 1\n    return x\n', ('None', '()', '(None,)')),
    ('def f() -> Optional[int]:\n    x = 1\n    return x\n', ('None', '0', '1')),
    ('def f() -> int | None:\n    x = 1\n    return x\n', ('None', '0', '1')),
    ("def f() -> 'int':\n    x = 1\n    return x\n", ('None', '0', '1')),
    ('def f() -> Thing:\n    x = 1\n    return x\n', ('None',)),
    ('def f() -> None:\n    x = 1\n', ('None',)),
    ('def f():\n    x = 1\n    return x > 0\n', ('None', 'True', 'False')),
    ('def f(x):\n    if x:\n        return f"{x}"\n    return "no"\n', ('None', "''", "'A'")),
    ('def f(x):\n    if x:\n        return 1\n    return "no"\n', ('None',)),
    ('def f(x):\n    print(x)\n', ('None',)),
    ('def f(x):\n    def g():\n        return 1\n    return True\n', ('None', 'True', 'False')),
    ('def f() -> None | int:\n    x = 1\n    return x\n', ('None', '0', '1')),
    ('def f(x):\n    return not x\n', ('None', 'True', 'False')),
    ('def f(x):\n    if x:\n        return True\n    return\n', ('None',)),
])
def test_values_follow_the_return_type(code, values):
    assert functions(code)[0].values == values


TYPED = 'def total(xs) -> int:\n    s = sum(xs)\n    return s + 5\n'
TYPED_TESTS = 'from svc import total\n\n\ndef test_total():\n    assert total([1]) is not None\n'


def project(root, files):
    import subprocess
    root.mkdir(parents=True, exist_ok=True)
    (root / 'pytest.ini').write_text('[pytest]\npythonpath = .\n')
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)
    if not (root / '.git').exists():
        subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=root, check=True)
    subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'files'], cwd=root, check=True)
    return root


@needs_coverage
def test_a_value_only_checked_against_none_is_partly_checked(tmp_path):
    from core.testminer.runner import mine
    root = project(tmp_path, {'svc.py': TYPED, 'tests/test_svc.py': TYPED_TESTS})
    item = mine(root, names=('svc.py::total',), command=pytest_command())['functions'][0]
    assert item['verdict'] == 'partly checked'
    assert item['values'] == [{'value': 'None', 'detected': True}, {'value': '0', 'detected': False},
                              {'value': '1', 'detected': False}]
    project(root, {'tests/test_svc.py': TYPED_TESTS.replace('is not None', '== 6')})
    exact = mine(root, names=('svc.py::total',), command=pytest_command())['functions'][0]
    assert exact['verdict'] == 'checked' and all(v['detected'] for v in exact['values'])
    project(root, {'tests/test_svc.py': TYPED_TESTS.replace('assert total([1]) is not None', 'total([1])')})
    assert mine(root, names=('svc.py::total',), command=pytest_command())['functions'][0]['verdict'] == \
        'reached, not checked'


@needs_coverage
def test_a_budget_between_two_values_gives_no_verdict(tmp_path, monkeypatch):
    from core.testminer import runner
    root = project(tmp_path, {'svc.py': TYPED, 'tests/test_svc.py': TYPED_TESTS})
    empty = runner._empty

    def late(path, fn, value='None'):
        if value != 'None':
            monkeypatch.setattr(runner.time, 'monotonic', lambda: float('inf'))
        empty(path, fn, value)
    monkeypatch.setattr(runner, '_empty', late)
    item = runner.mine(root, names=('svc.py::total',), command=pytest_command())['functions'][0]
    assert (item['verdict'], item['reason']) == ('unknown', 'budget')


@needs_coverage
def test_cli_names_the_values_no_test_noticed(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    root = project(tmp_path, {'svc.py': TYPED, 'tests/test_svc.py': TYPED_TESTS})
    cli = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_testminer.py'
    done = subprocess.run([sys.executable, str(cli), '--project', str(root), '--function', 'svc.py::total',
                           '--command', pytest_command()], capture_output=True, text=True)
    assert 'svc.py:2 total: partly checked (returning 0 or 1 failed no test)' in done.stdout, done.stdout + done.stderr


# Slice 2: record a real run.

APP = '''\
import other
import ignored_lib


def used():
    x = 1
    return x


def unused():
    x = 2
    return x


used()
other.ping()
ignored_lib.go()
'''
OTHER = 'def ping():\n    y = 1\n    return y\n'


def recorded(tmp_path, app=APP):
    root = project(tmp_path, {'app.py': app, 'other.py': OTHER, '.gitignore': '__pycache__/\nignored_lib.py\n'})
    (root / 'ignored_lib.py').write_text('def go():\n    z = 1\n    return z\n')
    return root


def porcelain(root):
    import subprocess
    return set(subprocess.run(['git', 'status', '--porcelain'], cwd=root, capture_output=True, text=True).stdout.splitlines())


@needs_coverage
def test_record_keeps_lines_and_hashes_of_tracked_files_only(tmp_path):
    import hashlib
    import sys
    from core.testminer.observe import OBSERVED, record
    root = recorded(tmp_path)
    before = porcelain(root)
    status, observation = record(root, [sys.executable, 'app.py', '--token', 'SECRET'])
    assert status == 0
    assert set(observation['files']) == {'app.py', 'other.py'}
    lines = observation['files']['app.py']['lines']
    assert 6 in lines and 11 not in lines
    assert observation['files']['other.py']['sha256'] == hashlib.sha256((root / 'other.py').read_bytes()).hexdigest()
    assert (observation['command'], observation['arguments']) == ('python app.py', 2)
    saved = (root / OBSERVED).read_text(encoding='utf-8')
    assert 'SECRET' not in saved and sys.executable not in saved
    assert porcelain(root) - before == {'?? .elevenpowers/'}


@needs_coverage
def test_record_saves_when_the_program_is_interrupted(tmp_path):
    import sys
    from core.testminer.observe import record
    root = recorded(tmp_path, APP + 'raise KeyboardInterrupt\n')
    status, observation = record(root, [sys.executable, 'app.py'])
    assert status != 0 and 6 in observation['files']['app.py']['lines']


@needs_coverage
def test_record_accepts_the_module_form_and_refuses_others(tmp_path, monkeypatch):
    import sys
    from core.testminer import observe
    root = project(tmp_path, {'pkg/__init__.py': '', 'pkg/__main__.py': 'def main():\n    v = 3\n    return v\n\n\nmain()\n'})
    status, observation = observe.record(root, [sys.executable, '-m', 'pkg', 'serve'])
    assert status == 0 and observation['command'] == 'python -m pkg' and observation['arguments'] == 1
    assert 3 in observation['files']['pkg/__main__.py']['lines']
    for words in (['node', 'x.js'], ['ep-no-such-tool', 'run'], [sys.executable, '-c', 'print(1)']):
        with pytest.raises(ValueError, match=r'python SCRIPT .*python -m MODULE'):
            observe.record(root, words)
    monkeypatch.setattr(observe, '_runs_as_module', lambda python, name: name == 'pkg')
    assert observe._target(['pkg', 'serve'])[1:] == (['-m', 'pkg', 'serve'], 'python -m pkg')


def test_record_without_coverage_names_the_install(tmp_path, monkeypatch):
    import sys
    from core.testminer import observe
    root = recorded(tmp_path)
    monkeypatch.setattr(observe, '_coverage_major', lambda python: 0)
    with pytest.raises(ValueError, match='pip install coverage'):
        observe.record(root, [sys.executable, 'app.py'])
    assert not (root / observe.OBSERVED).exists()
    with pytest.raises(ValueError) as refused:
        observe.record(root, ['node', 'x.js'])
    assert str(refused.value).isascii()


@needs_coverage
def test_a_file_changed_during_the_run_has_no_hash(tmp_path):
    import sys
    from core.testminer.observe import record
    root = recorded(tmp_path, APP + "open('other.py', 'a').write('# touched\\n')\n")
    _, observation = record(root, [sys.executable, 'app.py'])
    assert observation['files']['other.py']['sha256'] is None
    assert observation['files']['app.py']['sha256'] is not None


@needs_coverage
@pytest.mark.skipif(__import__('os').name == 'nt', reason='a POSIX process-group SIGINT, as Ctrl-C sends')
def test_ctrl_c_ends_the_program_and_the_record_is_saved(tmp_path):
    import os
    import signal
    import subprocess
    import sys
    import time
    from pathlib import Path
    serve = APP + "open('ready', 'w').close()\nimport time\nfor _ in range(300):\n    time.sleep(0.1)\n"
    root = recorded(tmp_path, serve)
    cli = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_testminer.py'
    process = subprocess.Popen([sys.executable, str(cli), 'record', '--project', str(root), '--',
                                sys.executable, 'app.py'], start_new_session=True)
    deadline = time.monotonic() + 30
    while not (root / 'ready').exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    os.killpg(process.pid, signal.SIGINT)
    process.wait(timeout=30)
    assert (root / '.elevenpowers/testminer-observed.json').exists()


OBSERVED_SVC = 'def used(x):\n    y = x + 1\n    return y\n\n\ndef unused(x):\n    y = x - 1\n    return y\n'
OBSERVED_FILES = {'svc.py': OBSERVED_SVC, 'app.py': 'from svc import used\n\nused(1)\n',
                  'tests/test_svc.py': 'from svc import used\n\n\ndef test_used():\n    assert used(1) == 2\n'}


def observed_project(tmp_path):
    import sys
    from core.testminer.observe import record
    root = project(tmp_path, OBSERVED_FILES)
    record(root, [sys.executable, 'app.py'])
    return root


@needs_coverage
def test_observed_selects_what_ran_and_never_what_did_not(tmp_path):
    from core.testminer.runner import mine
    root = observed_project(tmp_path)
    assert verdicts(mine(root, observed=True, command=pytest_command())) == {'used': 'checked'}


@needs_coverage
def test_an_edited_recorded_file_is_unknown_never_a_verdict(tmp_path):
    from core.testminer.observe import STALE
    from core.testminer.runner import mine
    root = observed_project(tmp_path)
    project(root, {'svc.py': OBSERVED_SVC + '# edited\n'})
    item = mine(root, observed=True, command=pytest_command())['functions']
    assert [(f['name'], f['verdict'], f['reason']) for f in item] == [('used', 'unknown', STALE)]
    named = mine(root, observed=True, names=('svc.py::used',), command=pytest_command())
    assert verdicts(named) == {'used': 'checked'}


@needs_coverage
def test_a_deleted_recorded_file_is_one_issue(tmp_path):
    from core.testminer.runner import mine
    root = observed_project(tmp_path)
    (root / 'app.py').unlink()
    project(root, {})
    result = mine(root, observed=True, command=pytest_command())
    assert any('app.py' in issue for issue in result['issues'])
    assert verdicts(result) == {'used': 'checked'}


CACHED = '''\
from functools import lru_cache


def names(x) -> list:
    out = []
    out.append(x)
    return out


@lru_cache()
def cached(x):
    return names(x)
'''
CACHED_TESTS = '''\
from svc import cached


def test_a_fills_the_cache():
    cached('a')


def test_b_checks_the_value():
    assert cached('a') == ['a']
'''


@needs_coverage
def test_a_test_served_from_a_cache_still_notices(tmp_path):
    # Found on charset_normalizer (2026-11-21): an lru_cache filled by one test hides the
    # function from the contexts of the test that checks it.
    from core.testminer.runner import mine
    root = project(tmp_path, {'svc.py': CACHED, 'tests/test_svc.py': CACHED_TESTS})
    item = mine(root, names=('svc.py::names',), command=pytest_command())['functions'][0]
    assert item['tests'] == ['test_svc.test_a_fills_the_cache']
    assert item['verdict'] == 'checked'


def test_observed_without_a_record_is_refused(tmp_path):
    from core.testminer.runner import mine
    root = project(tmp_path, OBSERVED_FILES)
    with pytest.raises(ValueError, match='ep_testminer.py record'):
        mine(root, observed=True, command='python -m pytest')


# Found by the slice 2 final review, 2026-11-21.

@needs_coverage
def test_record_refuses_a_project_outside_git_and_keeps_non_ascii_files(tmp_path):
    import sys
    from core.testminer.observe import record
    (tmp_path / 'plain').mkdir()
    (tmp_path / 'plain/app.py').write_text('x = 1\n')
    with pytest.raises(ValueError, match='not a Git repository'):
        record(tmp_path / 'plain', [sys.executable, 'app.py'])
    root = project(tmp_path / 'git', {'café.py': 'def brew():\n    c = 1\n    return c\n',
                                      'app.py': 'import importlib\nimportlib.import_module("caf\\u00e9").brew()\n'})
    _, observation = record(root, [sys.executable, 'app.py'])
    assert 'café.py' in observation['files']
