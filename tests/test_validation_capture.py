from core.hosts import validation


def test_capture_exports_only_qualified_fields(monkeypatch, tmp_path):
    monkeypatch.setattr(validation, 'fingerprint', lambda: 'a' * 64)
    monkeypatch.setattr(validation.acceptance, 'inspect', lambda *a: {
        'state': 'passed', 'language': 'python', 'runtime_fingerprint': 'a' * 64,
        'host_version': '1.2.3', 'checks': {'runtime_identity': True},
        'project': '/secret/path', 'next_actions': ['secret'], 'outcomes': {'pass': True, 'fail': True, 'incomplete': True}})
    monkeypatch.setattr(validation.probes, 'probe', lambda *a: {'state': 'observed', 'version': '1.2.3', 'source': 'installed_probe'})
    value = validation.capture('codex', tmp_path, observe_version=True)
    assert value['state'] == 'passed'
    assert value['version']['version'] == '1.2.3'
    assert 'secret' not in str(value)
    assert validation.capture('codex', tmp_path)['state'] != 'passed'


def test_runtime_moves_or_probe_version_conflicts(monkeypatch, tmp_path):
    monkeypatch.setattr(validation.acceptance, 'inspect', lambda *a: {
        'state': 'passed', 'language': 'python', 'runtime_fingerprint': 'a' * 64,
        'host_version': '1.2.3', 'checks': {}})
    monkeypatch.setattr(validation.probes, 'probe', lambda *a: {'state': 'observed', 'version': '2.2.3', 'source': 'installed_probe'})
    monkeypatch.setattr(validation, 'fingerprint', lambda: 'a' * 64)
    assert validation.capture('codex', tmp_path, observe_version=True)['state'] == 'incomplete'
    ids = iter(['a' * 64, 'b' * 64])
    monkeypatch.setattr(validation, 'fingerprint', lambda: next(ids))
    assert validation.capture('codex', tmp_path)['state'] == 'incomplete'
