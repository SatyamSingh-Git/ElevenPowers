"""Real producers must partition broad hunks and contain nested mutation spans."""
import sys
import time
import pytest
from core.strength.engines import cosmic, stryker
from core.strength.execution import Budget
from test_strength import stryker_path


@pytest.mark.parametrize('language', ['python', 'javascript'])
def test_new_whole_file_hunk_gives_distinct_functions_a_turn(tmp_path, language):
    if language == 'python':
        name, function = 'a.py', 'def {name}(x):\n    return x > 1\n\n'
        engine, executable = cosmic, sys.executable
    else:
        name, function = 'a.js', 'export function {name}(x) {{\n  return x > 1;\n}}\n'
        engine, executable = stryker, stryker_path()
    source = ''.join(function.format(name=n) for n in ('first','second','third'))
    (tmp_path/name).write_text(source)
    items, _ = engine(tmp_path, [name], executable, Budget(time.monotonic()+30,3),
                      {name:[[1,len(source.splitlines())]]})
    assert {c.context for c in items} == {'first','second','third'}


def test_inner_edit_cannot_mutate_outer_javascript_block(tmp_path):
    source = ('export function outer(x) {\n  function edited(y) {\n    return y > 1;\n  }\n'
              '  return edited(x) > 0;\n}\n')
    (tmp_path/'a.js').write_text(source)
    items, _ = stryker(tmp_path,['a.js'],stryker_path(),Budget(time.monotonic()+30,16),{'a.js':[[3,3]]})
    assert items
    assert all(2 <= c.line <= c.end_line <= 4 and c.context == 'edited' for c in items)
    assert all('return edited(x) > 0;' in c.content for c in items)
