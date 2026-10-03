"""Metadata boundaries and real execution controls for targeted observations."""
import json
import sys
import time
from types import SimpleNamespace

import pytest

from core.strength.engines import Candidate, generate
from core.strength.execution import Budget
from core.strength.model import Observation


@pytest.mark.parametrize('metadata', [
    {'line': 1000001}, {'end_line': 1000001}, {'end_line': True},
    {'end_line': 1}, {'relevance': 'whole_repository'}, {'context': 'bad\nname'},
])
def test_location_contract_rejects_malformed_ranges(metadata):
    fields = dict(id='m', path='a.py', line=2, operator='comparison', status='detected')
    fields.update(metadata)
    with pytest.raises(ValueError):
        Observation(**fields)
    fields.pop('status')
    with pytest.raises(ValueError):
        Candidate(**fields, content='value = 1\n')


def test_legacy_and_targeted_locations_survive_actual_attempts(tmp_path):
    from core.strength.mutations import run_candidate
    source = 'def edited(x):\n    return x > 0\n'
    (tmp_path / 'a.py').write_text(source)
    (tmp_path / 'test_a.py').write_text('from a import edited\ndef test_value():\n    assert edited(2)\n')
    legacy = Observation('old', 'a.py', 2, 'comparison', 'undetected')
    assert legacy.end_line == 2 and legacy.relevance == 'legacy_whole_file'
    candidate = Candidate('m', 'a.py', 2, 'comparison', source.replace('> 0', '>= 0'),
                          2, 'changed_lines', 'edited')
    value = run_candidate(candidate, tmp_path, f'"{sys.executable}" -m pytest -q -p no:cacheprovider',
                          Budget(time.monotonic() + 15, 1), 10)
    assert (value.status, value.line, value.end_line, value.relevance, value.context) == (
        'undetected', 2, 2, 'changed_lines', 'edited')
    assert (tmp_path / 'a.py').read_text() == source


@pytest.mark.parametrize('relation,line', [('legacy_whole_file', 2), ('changed_lines', 1),
                                         ('changed_function', 4)])
def test_targeted_adapter_rejects_unattributed_or_false_locations(tmp_path, monkeypatch, relation, line):
    from core.strength import engines
    (tmp_path / 'a.py').write_text('def edited(x):\n    return x > 0\n')
    response = {'version': '8.7.0', 'more': False, 'candidates': [{
        'id': 'm', 'path': 'a.py', 'line': line, 'end_line': line, 'operator': 'comparison',
        'content': 'def edited(x):\n    return x >= 0\n', 'relevance': relation, 'context': 'edited'}]}
    monkeypatch.setattr(engines, 'execute', lambda *a, **k: SimpleNamespace(
        status='complete', returncode=0, stdout=json.dumps(response)))
    with pytest.raises(ValueError, match='invalid or incomplete'):
        generate(tmp_path, ['a.py'], ['producer'], Budget(time.monotonic()+10, 2), {'a.py': [[2, 2]]})
