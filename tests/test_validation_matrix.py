from datetime import datetime, timezone

import pytest

from core.hosts import validation


def record():
    return {'schema_version': 1, 'kind': 'native_acceptance', 'host': 'codex',
            'language': 'python', 'state': 'passed', 'generated_at': datetime.now(timezone.utc).isoformat(),
            'runtime_fingerprint': 'a' * 64,
            'version': {'state': 'observed', 'version': '1.2.3', 'source': 'installed_probe'},
            'checks': {key: True for key in validation.CHECKS},
            'outcomes': {'pass': True, 'fail': True, 'incomplete': True}, 'limits': []}


def test_matrix_missing_duplicate_conflict_and_stale(monkeypatch):
    monkeypatch.setattr(validation, 'fingerprint', lambda: 'a' * 64)
    result = validation.matrix([record()])
    assert len(result['cells']) == 10
    assert result['passed'] == 1
    assert sum(c['state'] == 'waiting' for c in result['cells']) == 9
    assert validation.matrix([record(), record()])['passed'] == 0
    r = record(); r['checks']['startup_runtime'] = False
    assert validation.matrix([r])['passed'] == 0
    r = record(); r['runtime_fingerprint'] = 'b' * 64
    assert validation.matrix([r])['passed'] == 0


@pytest.mark.parametrize('field,value', [('schema_version', True), ('host', 'fake'),
                                          ('runtime_fingerprint', 'bad'), ('generated_at', 'bad')])
def test_malformed_input_is_rejected(monkeypatch, field, value):
    monkeypatch.setattr(validation, 'fingerprint', lambda: 'a' * 64)
    r = record(); r[field] = value
    with pytest.raises(ValueError):
        validation.matrix([r])


def test_non_boolean_or_unknown_fields_cannot_pass(monkeypatch):
    monkeypatch.setattr(validation, 'fingerprint', lambda: 'a' * 64)
    for r in (record(), record()):
        r['checks']['fresh_pipeline'] = 1
        with pytest.raises(ValueError):
            validation.matrix([r])
    r = record(); r['prompt'] = 'private'
    with pytest.raises(ValueError):
        validation.matrix([r])
