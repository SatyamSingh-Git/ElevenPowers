"""Real-engine and repository controls for relevant, isolated strength evidence."""
import sys
import time
from pathlib import Path

import pytest


@pytest.mark.parametrize('outside', [False, True])
def test_mutant_read_guard_keeps_original_root_and_allows_private_inputs(tmp_path, outside):
    from core.strength.baseline import baseline
    from core.strength.engines import Candidate
    from core.strength.execution import Budget
    from core.strength.mutations import run_candidate
    original = tmp_path/'original'
    copied = tmp_path/'copy'
    original.mkdir(); copied.mkdir()
    (original/'sentinel.txt').write_text('outside')
    (copied/'sentinel.txt').write_text('private')
    source = 'value = 1\n'
    (copied/'a.py').write_text(source)
    target = original/'sentinel.txt' if outside else copied/'sentinel.txt'
    (copied/'test_a.py').write_text(
        'from pathlib import Path\nimport a\n'
        'def test_value():\n'
        '    if a.value == 2:\n'
        f'        assert Path({str(target)!r}).read_text() == {"outside" if outside else "private"!r}\n'
        '    else:\n        assert a.value == 1\n')
    command = f'"{sys.executable}" -m pytest -q -p no:cacheprovider'
    assert baseline(command,copied,original,Budget(time.monotonic()+30,1),20).status == 'passed'
    observed = run_candidate(Candidate('one','a.py',1,'change','value = 2\n'),copied,
                             command,Budget(time.monotonic()+30,1),20,original=original)
    assert observed.status == ('error' if outside else 'undetected')
    assert (copied/'a.py').read_text() == source
