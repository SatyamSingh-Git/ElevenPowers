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
