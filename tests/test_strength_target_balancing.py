"""Actual engine controls for unequal files, nested edits and declared encodings."""
import sys
import time
import pytest
from core.strength.engines import cosmic, stryker
from core.strength.execution import Budget
from test_strength import stryker_path


@pytest.mark.parametrize('language', ['python', 'javascript'])
def test_file_with_many_changed_functions_cannot_take_all_first_turns(tmp_path, language):
    if language == 'python':
        extension, function = '.py', 'def {name}(x):\n    return x > 1\n\n'
        engine, executable = cosmic, sys.executable
    else:
        extension, function = '.js', 'export function {name}(x) {{\n  return x > 1;\n}}\n'
        engine, executable = stryker, stryker_path()
    a, b = 'a'+extension, 'b'+extension
    (tmp_path/a).write_text(''.join(function.format(name=n) for n in ('first','second','third')))
    (tmp_path/b).write_text(function.format(name='elsewhere'))
    candidates, _ = engine(tmp_path, [a,b], executable, Budget(time.monotonic()+30, 2),
                           {a:[[2,2],[5,5],[8,8]], b:[[2,2]]})
    assert {c.path for c in candidates} == {a,b}
    assert candidates.more


def test_python_declared_encoding_is_preserved_in_targeted_producer(tmp_path):
    source = '# coding: latin-1\n# caf\xe9\ndef edited(x):\n    return x > 1\n'
    (tmp_path/'a.py').write_bytes(source.encode('latin-1'))
    candidates, _ = cosmic(tmp_path, ['a.py'], sys.executable, Budget(time.monotonic()+30, 2),
                            {'a.py': [[4,4]]})
    assert candidates and all(c.context == 'edited' for c in candidates)
    assert (tmp_path/'a.py').read_bytes() == source.encode('latin-1')
