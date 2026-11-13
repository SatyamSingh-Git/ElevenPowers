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
