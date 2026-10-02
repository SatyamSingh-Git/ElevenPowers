"""New exercises bind preparation, native startup and current runtime."""
import json
from pathlib import Path

from test_native_acceptance import exercise_history


def test_prepared_exercise_records_runtime_identity(tmp_path):
    from core.hosts.acceptance import prepare
    from core.hosts.provenance import fingerprint
    source = Path(__file__).resolve().parents[1]
    value = prepare('codex', tmp_path / 'case', 'python', source, version='0.1.0')
    assert value['runtime_fingerprint'] == fingerprint(source)


def test_acceptance_rejects_changed_or_unbound_runtime(tmp_path, monkeypatch):
    from core.hosts.acceptance import inspect
    from core.hosts import provenance
    root = tmp_path / 'case'
    exercise_history(root, monkeypatch)
    assert inspect('codex', root)['state'] == 'passed'
    monkeypatch.setattr(provenance, 'fingerprint', lambda *args: 'b' * 64)
    changed = inspect('codex', root)
    assert changed['state'] == 'incomplete'
    assert not changed['checks']['runtime_identity']
    manifest_path = root / '.elevenpowers/acceptance.json'
    manifest = json.loads(manifest_path.read_text())
    manifest.pop('runtime_fingerprint', None)
    manifest_path.write_text(json.dumps(manifest))
    assert inspect('codex', root)['state'] != 'passed'
