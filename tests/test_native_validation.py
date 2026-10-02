"""Version-bound evidence controls; no model or installed host is launched."""
from pathlib import Path

import pytest


def source_tree(root):
    (root / 'core').mkdir(parents=True)
    (root / 'plugin/bin').mkdir(parents=True)
    (root / 'core/module.py').write_text('VALUE = 1\n')
    (root / 'plugin/bin/ep_hook.py').write_text('print("hook")\n')
    return root


def test_runtime_identity_changes_only_for_shipped_code(tmp_path):
    from core.hosts.provenance import fingerprint
    root = source_tree(tmp_path / 'one')
    other = source_tree(tmp_path / 'two')
    before = fingerprint(root)
    assert len(before) == 64 and before == fingerprint(other)
    (root / 'README.md').write_text('documentation only')
    (root / 'core/__pycache__').mkdir()
    (root / 'core/__pycache__/ignored.py').write_text('ignored')
    assert fingerprint(root) == before
    (root / 'core/module.py').write_text('VALUE = 2\n')
    assert fingerprint(root) != before


def test_runtime_identity_is_bounded_and_refuses_missing_tree(tmp_path, monkeypatch):
    from core.hosts import provenance
    root = source_tree(tmp_path / 'source')
    monkeypatch.setattr(provenance, 'MAX_FILES', 1)
    with pytest.raises(ValueError, match='limit'):
        provenance.fingerprint(root)
    monkeypatch.setattr(provenance, 'MAX_FILES', 512)
    monkeypatch.setattr(provenance, 'MAX_BYTES', 2)
    with pytest.raises(ValueError, match='limit'):
        provenance.fingerprint(root)
    with pytest.raises(ValueError, match='runtime'):
        provenance.fingerprint(tmp_path)


def test_runtime_identity_rejects_linked_code(tmp_path):
    from core.hosts.provenance import fingerprint
    root = source_tree(tmp_path / 'source')
    target = tmp_path / 'outside.py'
    target.write_text('secret')
    path = root / 'core/module.py'
    path.unlink()
    try:
        path.symlink_to(target)
    except OSError:
        pytest.skip('symlinks unavailable')
    with pytest.raises(ValueError, match='linked'):
        fingerprint(root)
