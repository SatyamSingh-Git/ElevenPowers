from pathlib import Path

import pytest

from core.hosts.bridge import run
from core.ledger import Ledger


def event(root, patch, identity='call-1', **extra):
    return {'cwd': str(root), 'session_id': 's', 'tool_use_id': identity,
            'tool_name': 'apply_patch', 'tool_input': {'command': patch}, **extra}


def test_native_patch_attributes_preexisting_dirty_file_without_git(tmp_path):
    file = tmp_path / 'service.py'
    file.write_text('already edited\n')
    patch = '*** Begin Patch\n*** Update File: service.py\n@@\n-already edited\n+changed again\n*** End Patch'
    payload = event(tmp_path, patch)
    run('codex', 'PreToolUse', payload)
    file.write_text('changed again\n')
    run('codex', 'PostToolUse', payload)
    ledger = Ledger.load(tmp_path)
    assert 'service.py' in ledger.touched
    assert not any(d['what'] == 'unattributed native edit' for d in ledger.decisions)


def test_patch_tracks_add_delete_and_move(tmp_path):
    (tmp_path / 'old.py').write_text('old\n')
    (tmp_path / 'gone.py').write_text('gone\n')
    patch = '*** Begin Patch\n*** Update File: old.py\n*** Move to: new.py\n@@\n-old\n+new\n*** Delete File: gone.py\n*** Add File: added.py\n+added\n*** End Patch'
    payload = event(tmp_path, patch)
    run('codex', 'PreToolUse', payload)
    (tmp_path / 'old.py').unlink()
    (tmp_path / 'gone.py').unlink()
    (tmp_path / 'new.py').write_text('new\n')
    (tmp_path / 'added.py').write_text('added\n')
    run('codex', 'PostToolUse', payload)
    assert set(Ledger.load(tmp_path).touched) == {'old.py', 'new.py', 'gone.py', 'added.py'}


@pytest.mark.parametrize('identity', ['', 'missing-pre'])
def test_missing_baseline_or_identity_preserves_coverage_gap(tmp_path, identity):
    patch = '*** Begin Patch\n*** Add File: added.py\n+added\n*** End Patch'
    payload = event(tmp_path, patch, identity)
    if not identity:
        run('codex', 'PreToolUse', payload)
    (tmp_path / 'added.py').write_text('added\n')
    run('codex', 'PostToolUse', payload)
    assert any(d['what'] == 'unattributed native edit' for d in Ledger.load(tmp_path).decisions)


def test_duplicate_post_does_not_invent_missing_baseline(tmp_path):
    payload = event(tmp_path, '*** Begin Patch\n*** Add File: added.py\n+added\n*** End Patch')
    run('codex', 'PreToolUse', payload)
    (tmp_path / 'added.py').write_text('added\n')
    run('codex', 'PostToolUse', payload)
    run('codex', 'PostToolUse', payload)
    ledger = Ledger.load(tmp_path)
    assert ledger.touched == ['added.py']
    assert not any(d['what'] == 'unattributed native edit' for d in ledger.decisions)


def test_outside_path_is_not_read_or_attributed(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    outside = tmp_path / 'private.py'
    outside.write_text('private secret')
    payload = event(project, '*** Begin Patch\n*** Update File: ../private.py\n@@\n-private secret\n+changed\n*** End Patch')
    run('codex', 'PreToolUse', payload)
    run('codex', 'PostToolUse', payload)
    ledger = Ledger.load(project)
    assert not ledger.touched
    assert any(d['what'] == 'unattributed native edit' for d in ledger.decisions)
    assert 'private secret' not in (project / '.elevenpowers/patches.json').read_text()


def test_interrupted_patch_attributes_partial_change_and_reports_gap(tmp_path):
    payload = event(tmp_path, '*** Begin Patch\n*** Add File: added.py\n+added\n*** End Patch')
    run('codex', 'PreToolUse', payload)
    (tmp_path / 'added.py').write_text('added\n')
    run('codex', 'PostToolUse', {**payload, 'is_interrupt': True})
    ledger = Ledger.load(tmp_path)
    assert ledger.touched == ['added.py']
    assert any(d['what'] == 'unattributed native edit' for d in ledger.decisions)


def test_same_content_patch_does_not_invent_an_edit(tmp_path):
    (tmp_path / 'service.py').write_text('same\n')
    payload = event(tmp_path, '*** Begin Patch\n*** Update File: service.py\n@@\n-same\n+same\n*** End Patch')
    run('codex', 'PreToolUse', payload)
    run('codex', 'PostToolUse', payload)
    assert not Ledger.load(tmp_path).touched


def test_baseline_cannot_cross_task_or_session(tmp_path):
    payload = event(tmp_path, '*** Begin Patch\n*** Add File: added.py\n+added\n*** End Patch')
    run('codex', 'PreToolUse', payload)
    (tmp_path / 'added.py').write_text('added\n')
    run('codex', 'PostToolUse', {**payload, 'session_id': 'other'})
    assert not Ledger.load(tmp_path).touched
    assert any(d['what'] == 'unattributed native edit' for d in Ledger.load(tmp_path).decisions)


def test_concurrent_duplicate_post_keeps_original_baseline(tmp_path, monkeypatch):
    from core.hosts import edits
    payload = event(tmp_path, '*** Begin Patch\n*** Add File: added.py\n+added\n*** End Patch')
    payload['_ep_platform'] = 'codex'
    edits.before(payload, tmp_path)
    (tmp_path / 'added.py').write_text('added\n')
    original = edits.snapshot
    nested = []
    def overlap(root, paths):
        monkeypatch.setattr(edits, 'snapshot', original)
        nested.append(edits.after(payload, root))
        return original(root, paths)
    monkeypatch.setattr(edits, 'snapshot', overlap)
    result = edits.after(payload, tmp_path)
    assert result == (['added.py'], [])
    assert nested == [result]


def test_changed_input_cannot_borrow_another_patch_baseline(tmp_path):
    payload = event(tmp_path, '*** Begin Patch\n*** Add File: a.py\n+a\n*** End Patch')
    run('codex', 'PreToolUse', payload)
    (tmp_path / 'a.py').write_text('a\n')
    wrong = event(tmp_path, '*** Begin Patch\n*** Add File: b.py\n+b\n*** End Patch')
    run('codex', 'PostToolUse', wrong)
    assert not Ledger.load(tmp_path).touched
    assert any(d['what'] == 'unattributed native edit' for d in Ledger.load(tmp_path).decisions)


def test_budget_exhaustion_does_not_hash_partial_file_as_complete(tmp_path, monkeypatch):
    from core.hosts import edits
    monkeypatch.setattr(edits, 'MAX_BYTES', 2)
    (tmp_path / 'service.py').write_text('large file\n')
    payload = event(tmp_path, '*** Begin Patch\n*** Update File: service.py\n@@\n-large file\n+new file\n*** End Patch')
    run('codex', 'PreToolUse', payload)
    (tmp_path / 'service.py').write_text('new file\n')
    run('codex', 'PostToolUse', payload)
    assert not Ledger.load(tmp_path).touched
    assert any(d['what'] == 'unattributed native edit' for d in Ledger.load(tmp_path).decisions)


def test_missing_session_identity_cannot_certify_edit_attribution(tmp_path):
    payload = event(tmp_path, '*** Begin Patch\n*** Add File: added.py\n+added\n*** End Patch')
    payload.pop('session_id')
    run('codex', 'PreToolUse', payload)
    (tmp_path / 'added.py').write_text('added\n')
    run('codex', 'PostToolUse', payload)
    assert not Ledger.load(tmp_path).touched
    assert any(d['what'] == 'unattributed native edit' for d in Ledger.load(tmp_path).decisions)


def test_patch_missing_post_event_is_reported_at_completion(tmp_path):
    from core.config import Config, save
    save(tmp_path, Config(profile='guide'))
    payload = event(tmp_path, '*** Begin Patch\n*** Add File: added.py\n+added\n*** End Patch')
    run('codex', 'PreToolUse', payload)
    (tmp_path / 'added.py').write_text('added\n')
    run('codex', 'Stop', {'cwd': str(tmp_path), 'session_id': 's'})
    ledger = Ledger.load(tmp_path)
    assert ledger.touched == ['added.py']
    assert any(d['what'] == 'unattributed native edit' for d in ledger.decisions)


def test_patch_explicit_other_workdir_does_not_attribute_root_paths(tmp_path):
    nested = tmp_path / 'other'
    nested.mkdir()
    payload = event(tmp_path, '*** Begin Patch\n*** Add File: added.py\n+added\n*** End Patch')
    payload['tool_input']['workdir'] = str(nested)
    run('codex', 'PreToolUse', payload)
    (tmp_path / 'added.py').write_text('unrelated root edit\n')
    run('codex', 'PostToolUse', payload)
    assert not Ledger.load(tmp_path).touched
    assert any(d['what'] == 'unattributed native edit' for d in Ledger.load(tmp_path).decisions)


def test_evicted_pending_call_keeps_a_durable_coverage_gap(tmp_path, monkeypatch):
    from core.hosts import edits
    from core.obligations import Claim
    from core.ledger import Status
    monkeypatch.setattr(edits, 'MAX_PENDING', 1)
    ledger = Ledger(root=tmp_path, task='docs', request='Update project docs', claims=[Claim.DOCS_CHANGED])
    ledger.save()
    patch = '*** Begin Patch\n*** Add File: added.py\n+added\n*** End Patch'
    run('codex', 'PreToolUse', event(tmp_path, patch, 'abandoned'))
    run('codex', 'PreToolUse', event(tmp_path, patch, 'new-call'))
    # Complete the retained call with no edit; the evicted uncertainty remains.
    run('codex', 'PostToolUse', event(tmp_path, patch, 'new-call'))
    assert Ledger.load(tmp_path).status() == Status.UNVERIFIED
    run('codex', 'Stop', {'cwd': str(tmp_path), 'session_id': 's'})
    assert any(d['what'] == 'unattributed native edit' for d in Ledger.load(tmp_path).decisions)


def test_pending_call_is_visible_before_completion(tmp_path):
    from core.obligations import Claim
    from core.ledger import Status
    from core.status import render
    ledger = Ledger(root=tmp_path, task='docs', request='Update project docs', claims=[Claim.DOCS_CHANGED])
    ledger.save()
    run('codex', 'PreToolUse', event(tmp_path, '*** Begin Patch\n*** Add File: added.py\n+added\n*** End Patch'))
    assert Ledger.load(tmp_path).status() == Status.UNVERIFIED
    assert 'native edit coverage' in render(tmp_path).lower()
