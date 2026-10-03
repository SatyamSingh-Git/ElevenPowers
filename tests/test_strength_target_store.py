"""Forward and hostile saved-record controls, including historical schema 1."""
from copy import deepcopy
import pytest
from core.strength.store import load, save, validate


def record():
    return {'schema_version': 2, 'task': 't', 'state': 'incomplete', 'issues': ['attempt limit'],
            'observations': [], 'fingerprint': '', 'source_fingerprint': '', 'baseline': 'passed',
            'engine_versions': {}, 'base': 'b', 'command': 'pytest', 'settings': {},
            'paths': ['a.py'], 'recorded_at': 1, 'summary': {}, 'attempts': 0, 'limitations': [],
            'selection': {'strategy': 'changed_functions_and_hunks', 'regions': {'a.py': [[2, 2]]},
                          'deletion_anchors': {'a.py': [1]}},
            'command_coverage': {'scope': 'recorded_command_only', 'origin': 'configured'}}


def test_targeted_and_original_saved_schemas_round_trip(tmp_path):
    value = record()
    save(tmp_path, value)
    assert load(tmp_path, 't')['selection'] == value['selection']
    old = deepcopy(value)
    old['schema_version'] = 1
    old.pop('selection'); old.pop('command_coverage')
    save(tmp_path, old)
    assert load(tmp_path, 't')['schema_version'] == 1


@pytest.mark.parametrize('version', [True, 1.0, 2.0, '2', 3])
def test_schema_version_requires_exact_supported_integer(version):
    value = record()
    value['schema_version'] = version
    if version == 1:
        value.pop('selection'); value.pop('command_coverage')
    with pytest.raises(ValueError):
        validate(value)


@pytest.mark.parametrize('field,replacement', [
    ('regions', {'elsewhere.py': [[2, 2]]}), ('regions', {'a.py': [[3, 2]]}),
    ('regions', {'a.py': [[True, 2]]}), ('deletion_anchors', {'elsewhere.py': [1]}),
    ('deletion_anchors', {'a.py': [0]}),
])
def test_invalid_attribution_does_not_replace_previous_record(tmp_path, field, replacement):
    value = record()
    save(tmp_path, value)
    value['selection'][field] = replacement
    with pytest.raises(ValueError):
        save(tmp_path, value)
    assert load(tmp_path, 't')['selection'] == record()['selection']
