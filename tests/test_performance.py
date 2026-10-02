import pytest

from core.hosts import performance


def health_value(state='waiting'):
    return {'health': {'state': state}, 'coverage': {'complete': True, 'files': 2, 'bytes': 20},
            'timings': {'health_read_ms': 10., 'source_snapshot_ms': 2., 'report_ms': 5.},
            'activation': {'phases': {}}, 'task_state': 'UNVERIFIED',
            'report_coverage': {'source_fingerprint': 'b' * 64}}


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


def test_retained_callbacks_are_not_multiplied_and_stop_is_qualified(monkeypatch, tmp_path):
    monkeypatch.setattr(performance, 'fingerprint', lambda: 'a' * 64)
    value = health_value()
    value['activation']['phases'] = {'Stop': {'samples_ms': [1., 9.]}, 'Secret': {'samples_ms': [2.]}}
    monkeypatch.setattr(performance.health, 'inspect', lambda *a, **kw: value)
    result = performance.measure('claude', tmp_path)
    assert result['retained_callbacks']['Stop']['samples'] == 2
    assert 'Secret' not in str(result)
    assert any('verification' in limit and 'Stop' in limit for limit in result['limits'])
    value['timings']['report_ms'] = float('inf')
    assert performance.measure('claude', tmp_path)['state'] == 'incomplete'


def test_cooperative_deadline_stops_scheduling(monkeypatch, tmp_path):
    monkeypatch.setattr(performance, 'fingerprint', lambda: 'a' * 64)
    clock = [0.]
    monkeypatch.setattr(performance.time, 'monotonic', lambda: clock[0])
    def inspect(*a, **kw):
        clock[0] += 2
        return health_value()
    monkeypatch.setattr(performance.health, 'inspect', inspect)
    value = performance.measure('codex', tmp_path, timeout=1)
    assert value['attempted'] == 1 and value['state'] == 'incomplete'
