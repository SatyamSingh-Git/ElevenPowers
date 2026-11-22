"""Forward and adversarial controls for changed-region strength analysis."""
import sys
import time
from pathlib import Path
import pytest


def test_real_cosmic_sample_reaches_late_changed_function_without_unrelated_mutants(tmp_path):
    import importlib.util
    from core.strength.engines import cosmic
    from core.strength.execution import Budget
    if importlib.util.find_spec('cosmic_ray') is None:
        pytest.skip('optional cosmic-ray not installed')
    (tmp_path/'a.py').write_text('def unrelated(x):\n    return x > 0\n\ndef edited(x):\n    return x > 1\n')
    items,version = cosmic(tmp_path,['a.py'],sys.executable,Budget(time.monotonic()+30,4),
                           {'a.py':[[5,5]]})
    assert version == '8.7.0' and items
    assert all(c.line >= 4 and c.context == 'edited' for c in items)
    assert all(c.relevance in ('changed_lines','changed_function') for c in items)
    assert all('def unrelated(x):\n    return x > 0' in c.content for c in items)


def test_real_cosmic_small_sample_gives_each_changed_file_a_turn(tmp_path):
    from core.strength.engines import cosmic
    from core.strength.execution import Budget
    for name in ('a.py','b.py'):
        (tmp_path/name).write_text('def edited(x):\n    return x > 1\n')
    items,_ = cosmic(tmp_path,['a.py','b.py'],sys.executable,Budget(time.monotonic()+30,2),
                     {'a.py':[[2,2]],'b.py':[[2,2]]})
    assert {c.path for c in items} == {'a.py','b.py'}


def test_changed_comment_does_not_fall_back_to_unrelated_whole_file_mutation(tmp_path):
    from core.strength.engines import cosmic
    from core.strength.execution import Budget
    (tmp_path/'a.py').write_text('# changed comment\n\ndef untouched(x):\n    return x > 1\n')
    items,_ = cosmic(tmp_path,['a.py'],sys.executable,Budget(time.monotonic()+30,4),{'a.py':[[1,1]]})
    assert not items and not items.more


def test_type_annotations_are_never_mutated_and_code_beside_them_still_is(tmp_path):
    # Found on held-out agent changes (2026-11-22): `key: str | bytes` became `str + bytes`.
    # Under `from __future__ import annotations` that line never runs, so every such mutant
    # survived and the review listed the signature as a line no test noticed.
    import importlib.util
    from core.strength.engines import cosmic
    from core.strength.execution import Budget
    if importlib.util.find_spec('cosmic_ray') is None:
        pytest.skip('optional cosmic-ray not installed')
    source = ('from __future__ import annotations\n\n\n'
              'def merge(key: str | bytes, flags: int | None = None) -> bytes | None:\n'
              '    limit: int | None = 3\n'
              '    return key if flags | 1 else limit\n\n\n'
              'def café(naïve: int | None) -> int:\n'
              '    return naïve | 2\n\n\n'
              # Columns are characters for Cosmic Ray, bytes for ast: six accented letters before
              # `int` would stretch a byte-counted span over the default `4 | 1`.
              'def über(ééééé: int = 4 | 1) -> int:\n'
              '    return ééééé\n')
    (tmp_path / 'a.py').write_text(source, encoding='utf-8')
    kept = ('key: str | bytes', 'flags: int | None', '-> bytes | None', 'limit: int | None', 'naïve: int | None')
    for regions in ({'a.py': [[4, 14]]}, None):
        items, _ = cosmic(tmp_path, ['a.py'], sys.executable, Budget(time.monotonic() + 60, 400), regions)
        assert not items.more, 'the sample must reach every line'
        for text in kept:
            assert all(text in c.content for c in items), (text, regions)
        for mutated in ('flags + 1', 'naïve + 2', '= 4 + 1)'):
            assert any(mutated in c.content for c in items), (mutated, regions)
