"""Declarations never grant external filesystem approval."""
import json
from pathlib import Path
import time

import pytest


def policy(root, **extra):
    value = {'schema': 1, 'witnesses': [{'id': 'dependencies', 'root': 'deps', 'paths': ['parser.py']}]}
    value.update(extra)
    (root/'elevenpowers.inputs.json').write_text(json.dumps(value))
    return value


def test_no_policy_and_valid_literal_declarations(tmp_path):
    from core.inputs.definition import load
    assert load(tmp_path) is None
    policy(tmp_path)
    value = load(tmp_path)
    assert value['witnesses'][0]['paths'] == ['parser.py']
    assert value['limits'] == {'files': 2048, 'bytes': 32*1024*1024, 'seconds': 10}


@pytest.mark.parametrize('path', ['../secret', '/absolute', 'C:/secret', 'C:secret', r'folder\file', 'a/../b', '', 'a//b', '*.py', 'a\0b'])
def test_nonliteral_or_escaping_paths_are_refused(tmp_path, path):
    from core.inputs.definition import load
    policy(tmp_path, witnesses=[{'id':'w','root':'deps','paths':[path]}])
    with pytest.raises(ValueError):
        load(tmp_path)


@pytest.mark.parametrize('raw', ['{"schema":1,"schema":1,"witnesses":[]}',
    '{"schema":1,"witnesses":[],"limits":{"seconds":NaN}}',
    '{"schema":1,"witnesses":[],"unknown":true}', '{"schema":true,"witnesses":[]}',
    '{"schema":1,"witnesses":[]}', '{"schema":1,"witnesses":null}'])
def test_strict_policy_refuses_ambiguous_or_empty_configuration(tmp_path, raw):
    from core.inputs.definition import load
    (tmp_path/'elevenpowers.inputs.json').write_text(raw)
    with pytest.raises(ValueError):
        load(tmp_path)


def test_duplicate_ids_unknown_witness_fields_and_limits_are_refused(tmp_path):
    from core.inputs.definition import load
    value = policy(tmp_path)
    for bad in [dict(witnesses=value['witnesses']*2),
                dict(witnesses=[{**value['witnesses'][0], 'command':'run something'}]),
                dict(limits={'files':0}), dict(limits={'bytes':257*1024*1024}),
                dict(limits={'seconds':float('inf')}), dict(limits={'extra':1})]:
        policy(tmp_path, **bad)
        with pytest.raises(ValueError):
            load(tmp_path)


def test_oversized_or_linked_policy_is_refused(tmp_path):
    from core.inputs.definition import load
    target = tmp_path/'elevenpowers.inputs.json'
    target.write_bytes(b' '*65537)
    with pytest.raises(ValueError):
        load(tmp_path)
    target.unlink()
    other = tmp_path/'elsewhere.json'
    other.write_text('{}')
    try:
        target.symlink_to(other)
    except OSError:
        pytest.skip('symlinks unavailable')
    with pytest.raises(ValueError):
        load(tmp_path)


def test_real_atomic_replacement_keeps_legitimate_reads_available(tmp_path):
    from core.inputs.bindings import _write
    from core.inputs.definition import raw
    path = tmp_path/'state'
    path.write_bytes(b'original')
    for _ in range(20):
        _write(path, b'actual unchanged replacement bytes')
        assert raw(path) == b'actual unchanged replacement bytes'


def test_explicit_binding_preserves_ignore_rules_and_requires_replace(tmp_path):
    from core.inputs.bindings import bind, load
    from core.inputs.definition import load as definition
    root = tmp_path/'project'; root.mkdir()
    directory = tmp_path/'deps'; directory.mkdir()
    other = tmp_path/'other'; other.mkdir()
    policy(root)
    state = root/'.elevenpowers'; state.mkdir()
    (state/'.gitignore').write_text('existing.private\n')
    bind(root, 'deps', directory)
    assert (state/'.gitignore').read_text().startswith('existing.private\n')
    assert 'input-roots.json' in (state/'.gitignore').read_text()
    assert load(root, definition(root), time.monotonic()+10)['roots']['deps'] == str(directory.resolve())
    with pytest.raises(ValueError):
        bind(root, 'deps', other)
    bind(root, 'deps', other, replace=True)
    assert load(root, definition(root), time.monotonic()+10)['roots']['deps'] == str(other.resolve())


def test_unapproved_and_copied_bindings_are_refused(tmp_path):
    from core.inputs.bindings import bind, load
    from core.inputs.definition import load as definition
    root = tmp_path/'one'; root.mkdir(); policy(root)
    directory = tmp_path/'deps'; directory.mkdir()
    with pytest.raises(ValueError):
        load(root, definition(root), time.monotonic()+10)
    with pytest.raises(ValueError):
        bind(root, 'unknown', directory)
    bind(root, 'deps', directory)
    second = tmp_path/'two'; second.mkdir(); policy(second)
    (second/'.elevenpowers').mkdir()
    (second/'.elevenpowers/input-roots.json').write_bytes((root/'.elevenpowers/input-roots.json').read_bytes())
    with pytest.raises(ValueError):
        load(second, definition(second), time.monotonic()+10)


def test_explicit_replace_can_repair_removed_root_and_unused_roots_do_not_block(tmp_path):
    from core.inputs.bindings import bind, load
    from core.inputs.definition import load as definition
    root = tmp_path/'project'; root.mkdir()
    policy(root, witnesses=[{'id':'main','root':'deps','paths':['parser.py']},
                           {'id':'optional','root':'old','paths':['.']}])
    initial = tmp_path/'initial'; initial.mkdir()
    unused = tmp_path/'unused'; unused.mkdir()
    replacement = tmp_path/'replacement'; replacement.mkdir()
    bind(root,'deps',initial); bind(root,'old',unused)
    initial.rmdir()
    bind(root,'deps',replacement,replace=True)
    unused.rmdir()
    policy(root)
    assert load(root,definition(root),time.monotonic()+10)['roots']['deps'] == str(replacement.resolve())


def test_state_ancestors_and_linked_binding_roots_are_refused(tmp_path):
    from core.inputs.bindings import bind
    root = tmp_path/'project'; root.mkdir(); policy(root)
    state = root/'.elevenpowers'; state.mkdir()
    git_state = root/'.git'; git_state.mkdir()
    for directory in [root, tmp_path, state, git_state]:
        with pytest.raises(ValueError):
            bind(root, 'deps', directory)
    target = tmp_path/'deps'; target.mkdir()
    link = tmp_path/'link'
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip('directory links unavailable')
    with pytest.raises(ValueError):
        bind(root, 'deps', link)


def test_git_tracked_approval_cannot_qualify_as_local(tmp_path):
    from core.inputs.bindings import bind, load
    from core.inputs.definition import load as definition
    from tests.test_patchproof_identity import git
    root = tmp_path/'project'; root.mkdir(); policy(root)
    directory = tmp_path/'deps'; directory.mkdir()
    git(root, 'init', '-q')
    bind(root, 'deps', directory)
    git(root, 'add', '-f', '.elevenpowers/input-roots.json')
    with pytest.raises(ValueError):
        load(root, definition(root), time.monotonic()+10)
    with pytest.raises(ValueError):
        bind(root, 'deps', directory, replace=True)


def test_git_environment_redirect_cannot_hide_tracked_approval(tmp_path,monkeypatch):
    from core.inputs.bindings import bind,load
    from core.inputs.definition import load as definition
    from tests.test_patchproof_identity import git
    root = tmp_path/'project'; root.mkdir(); policy(root)
    other = tmp_path/'other'; other.mkdir()
    directory = tmp_path/'deps'; directory.mkdir()
    git(root,'init','-q'); git(other,'init','-q')
    bind(root,'deps',directory)
    git(root,'add','-f','.elevenpowers/input-roots.json')
    monkeypatch.setenv('GIT_DIR',str(other/'.git'))
    with pytest.raises(ValueError):
        load(root,definition(root),time.monotonic()+10)
