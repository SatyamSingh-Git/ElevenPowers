"""Forward and adversarial controls for changed-region strength analysis."""
import sys
import time
from pathlib import Path
import pytest


@pytest.mark.parametrize('suffix', ['js','ts','tsx'])
def test_real_stryker_sample_reaches_changed_function_and_keeps_other_functions(tmp_path,suffix):
    from core.strength.engines import stryker
    from core.strength.execution import Budget
    from test_strength import stryker_path
    engine = stryker_path()
    annotation = ': number' if suffix != 'js' else ''
    source = f'export function old(x{annotation}) {{\n  return x > 0;\n}}\nexport function edited(x{annotation}) {{\n  return x > 1;\n}}\n'
    name = 'a.'+suffix
    (tmp_path/name).write_text(source)
    items,version = stryker(tmp_path,[name],engine,Budget(time.monotonic()+30,4),{name:[[5,5]]})
    assert version == '9.5.1' and items
    assert all(c.line >= 4 and c.context == 'edited' for c in items)
    assert all(c.relevance in ('changed_lines','changed_function') for c in items)
    assert all(f'return x > 0;' in c.content for c in items)
