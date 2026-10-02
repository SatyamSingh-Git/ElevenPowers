import pytest

from core.hosts import performance


def health_value(state='waiting'):
    return {'health': {'state': state}, 'coverage': {'complete': True, 'files': 2, 'bytes': 20},
            'timings': {'health_read_ms': 10., 'source_snapshot_ms': 2., 'report_ms': 5.},
            'activation': {'phases': {}}, 'task_state': 'UNVERIFIED'}


def test_every_attempt_retained_including_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(performance, 'fingerprint', lambda: 'a' * 64)
    samples = iter([health_value(), OSError('private'), health_value('incomplete')])
    def inspect(*a, **kw):
        value = next(samples)
        if isinstance(value, Exception):
            raise value
        return value
    monkeypatch.setattr(performance.health, 'inspect', inspect)
    result = performance.measure('codex', tmp_path)
    assert len(result['samples']) == 3
    assert [v['state'] for v in result['samples']] == ['complete', 'failed', 'complete']
    assert result['state'] == 'incomplete'
    assert 'private' not in str(result)
    assert result['warmup'] == 'none; every attempted read retained'


def test_deadline_and_runtime_movement_not_success(monkeypatch, tmp_path):
    ids = iter(['a' * 64, 'b' * 64])
    monkeypatch.setattr(performance, 'fingerprint', lambda: next(ids))
    monkeypatch.setattr(performance.health, 'inspect', lambda *a, **kw: health_value())
    assert performance.measure('codex', tmp_path, repeats=1)['state'] == 'incomplete'
    with pytest.raises(ValueError):
        performance.measure('codex', tmp_path, timeout=float('nan'))
    with pytest.raises(ValueError):
        performance.measure('codex', tmp_path, repeats=True)
