"""Real repository controls; expectations come from independently created commits."""
import hashlib
import os
from pathlib import Path
import subprocess

import pytest


def git(root, *args):
    return subprocess.check_output(['git', '-c', f'safe.directory={root.as_posix()}',
                                    *args], cwd=root).strip()


def commit(root, message):
    git(root, 'add', '--all')
    git(root, '-c', 'user.name=Patch control', '-c', 'user.email=control@example.invalid',
        'commit', '-qm', message)
    return git(root, 'rev-parse', 'HEAD').decode()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'config', 'core.autocrlf', 'false')
    (tmp_path / 'service.py').write_bytes(b'value = 1\n')
    base = commit(tmp_path, 'base')
    (tmp_path / 'service.py').write_bytes(b'value = 2\n')
    head = commit(tmp_path, 'patch')
    return tmp_path, base, head


def test_exact_commits_and_tree_pair_are_reproducible(repo):
    from core.patchproof.identity import collect
    root, base, head = repo
    before = (root / '.git/index').read_bytes()
    value = collect(root, base, head)
    assert value['complete'] and value['state'] == 'available'
    assert value['base'] == base and value['head'] == head
    assert value['base_tree'] == git(root, 'rev-parse', base + '^{tree}').decode()
    assert value['head_tree'] == git(root, 'rev-parse', head + '^{tree}').decode()
    assert value['changes'][0]['path'] == 'service.py'
    assert value['changes'][0]['kind'] == 'M'
    assert value['checkout']['eligible']
    assert value['patch_id'] == collect(root, base, head)['patch_id']
    assert value['patch_id'] != collect(root, head, base)['patch_id']
    assert before == (root / '.git/index').read_bytes()


def test_empty_range_is_distinct_from_unavailable_ref(repo):
    from core.patchproof.identity import collect
    root, base, head = repo
    empty = collect(root, head, head)
    assert empty['empty'] and empty['complete'] and not empty['changes']
    missing = collect(root, 'does-not-exist', head)
    assert not missing['complete'] and missing['empty'] is None
    assert missing['issues'] and not missing['patch_id']


@pytest.mark.parametrize('change', ['worktree', 'index', 'untracked'])
def test_checkout_changes_prevent_clean_binding(repo, change):
    from core.patchproof.identity import collect
    root, base, head = repo
    path = root / ('untracked.py' if change == 'untracked' else 'service.py')
    path.write_bytes(b'value = 99\n')
    if change == 'index':
        git(root, 'add', '--all')
    value = collect(root, base, head)
    assert value['complete']  # Committed identity remains collectable.
    assert not value['checkout']['eligible']
    assert value['checkout']['issues']


def test_different_checkout_and_nested_project_are_explicit(repo):
    from core.patchproof.identity import collect
    root, base, head = repo
    value = collect(root, head, base)
    assert value['complete'] and not value['checkout']['eligible']
    child = root / 'child'
    child.mkdir()
    nested = collect(child, base, head)
    assert not nested['complete'] and nested['issues']


def test_rename_deletion_binary_and_odd_paths_keep_object_identity(repo):
    from core.patchproof.identity import collect
    root, base, head = repo
    (root / 'service.py').rename(root / '-session ü space.py')
    (root / 'binary.bin').write_bytes(b'\x00\xff\r\n')
    end = commit(root, 'rename and binary')
    value = collect(root, head, end)
    rename = next(c for c in value['changes'] if c['kind'] == 'R')
    assert rename['old_path'] == 'service.py'
    assert rename['path'] == '-session ü space.py'
    assert rename['old_blob'] == rename['new_blob']
    binary = next(c for c in value['changes'] if c['path'] == 'binary.bin')
    assert binary['binary'] and binary['new_blob'] != '0' * 40
    (root / 'binary.bin').unlink()
    deleted = commit(root, 'delete')
    assert collect(root, end, deleted)['changes'][0]['kind'] == 'D'


def test_deadline_and_leading_dash_ref_never_become_empty_success(repo):
    from core.patchproof.identity import collect
    root, base, head = repo
    for value in (collect(root, base, head, seconds=0), collect(root, '--help', head)):
        assert not value['complete'] and value['empty'] is None
        assert value['issues']


def test_linked_worktree_has_its_own_checkout_identity(repo, tmp_path):
    from core.patchproof.identity import collect
    root, base, head = repo
    linked = root.parent / (root.name + '-linked')
    git(root, 'worktree', 'add', '--detach', str(linked), head)
    try:
        value = collect(linked, base, head)
        assert value['complete'] and value['checkout']['eligible']
    finally:
        git(root, 'worktree', 'remove', '--force', str(linked))


def test_configured_git_helpers_are_not_executed(repo):
    from core.patchproof.identity import collect
    root, base, head = repo
    marker = root / 'helper-ran'
    command = 'echo invoked > helper-ran'
    for key in ('core.fsmonitor', 'diff.external', 'diff.private.textconv',
                'filter.private.clean', 'filter.private.process'):
        git(root, 'config', key, command)
    (root / '.gitattributes').write_bytes(b'*.py diff=private filter=private\n')
    # Keep attributes untracked: no Git operation with these helpers is needed.
    value = collect(root, base, head)
    assert value['complete']
    assert not marker.exists()
    assert not value['checkout']['eligible']


def test_submodule_and_symlink_modes_are_qualified_without_following(repo):
    from core.patchproof.identity import collect
    root, base, head = repo
    # Construct tree entries directly, independent of OS symlink privileges.
    blob = git(root, 'hash-object', 'service.py').decode()
    git(root, 'update-index', '--add', '--cacheinfo', f'120000,{blob},link')
    git(root, 'update-index', '--add', '--cacheinfo', f'160000,{base},vendor')
    git(root, '-c', 'user.name=Control', '-c', 'user.email=c@example.invalid',
        'commit', '-qm', 'linked inputs')
    end = git(root, 'rev-parse', 'HEAD').decode()
    value = collect(root, head, end)
    assert value['complete']
    assert not value['checkout']['eligible']
    assert any('linked' in issue or 'submodule' in issue for issue in value['checkout']['issues'])


def test_non_git_root_remains_unavailable(tmp_path):
    from core.patchproof.identity import collect
    value = collect(tmp_path, 'HEAD~1', 'HEAD')
    assert not value['complete'] and value['empty'] is None

