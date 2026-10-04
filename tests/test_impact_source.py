"""Graph controls distinguish actual relationships from name resemblance."""
import os
import subprocess

import pytest


def put(root, path, text):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text, encoding='utf-8')
    return file


def graph(root, **kwargs):
    from core.impact import build
    return build(root, **kwargs)


def links(value, kind='imports'):
    return {(e.source, e.target) for e in value.edges if e.kind == kind}


def test_import_alias_call_and_unrelated_same_name(tmp_path):
    put(tmp_path, 'session.py', 'def expire():\n    return 1\n')
    put(tmp_path, 'api.py', 'from session import expire as renew\nrenew()\n')
    put(tmp_path, 'unrelated.py', 'def expire():\n    return 2\nexpire()\n')
    value = graph(tmp_path)
    assert ('file:api.py', 'file:session.py') in links(value)
    assert ('file:api.py', 'symbol:session.py#expire') in links(value, 'calls')
    assert ('file:unrelated.py', 'symbol:session.py#expire') not in links(value, 'calls')
    edge = next(e for e in value.edges if e.kind == 'calls')
    assert (edge.origin, edge.path, edge.line) == ('static', 'api.py', 2)
    assert value.to_dict()['schema'] == 1


@pytest.mark.parametrize('path,source', [
    ('src/app/api.py', 'from .session import expire\nexpire()\n'),
    ('api.py', 'from app.session import expire\nexpire()\n'),
    ('src/app/api.py', 'from . import session\nsession.expire()\n'),
    ('api.py', 'import app.session as s\ns.expire()\n'),
    ('api.py', 'import app.session\napp.session.expire()\n'),
])
def test_package_and_src_imports(tmp_path, path, source):
    put(tmp_path, 'src/app/__init__.py', '')
    put(tmp_path, 'src/app/session.py', 'def expire():\n    return 1\n')
    put(tmp_path, path, source)
    value = graph(tmp_path)
    assert (f'file:{path}', 'file:src/app/session.py') in links(value)
    assert (f'file:{path}', 'symbol:src/app/session.py#expire') in links(value, 'calls')


@pytest.mark.parametrize('source', [
    'from session import expire\ndef use(expire):\n    expire()\n',
    'from session import expire\nexpire = lambda: 2\nexpire()\n',
    'from session import expire\ndef use():\n    expire = lambda: 2\n    expire()\n',
    'from session import expire\nclass C:\n    def expire(self): pass\n    def use(self): self.expire()\n',
])
def test_shadows_do_not_become_imported_calls(tmp_path, source):
    put(tmp_path, 'session.py', 'def expire(): pass\n')
    put(tmp_path, 'api.py', source)
    assert not links(graph(tmp_path), 'calls')


def test_ambiguous_short_module_is_a_gap(tmp_path):
    put(tmp_path, 'a/session.py', 'def expire(): pass\n')
    put(tmp_path, 'b/session.py', 'def expire(): pass\n')
    put(tmp_path, 'api.py', 'from session import expire\nexpire()\n')
    value = graph(tmp_path)
    assert not links(value)
    assert 'ambiguous' in ' '.join(value.issues)


def test_parser_failure_is_not_a_complete_empty_model(tmp_path):
    put(tmp_path, 'broken.py', 'def broken(:\n')
    value = graph(tmp_path)
    assert 'parse' in ' '.join(value.issues)
    assert not value.coverage['complete']


def test_dirty_bytes_add_delete_and_rename_change_fingerprint(tmp_path):
    path = put(tmp_path, 'session.py', 'value=1\n')
    before = graph(tmp_path).fingerprint
    stamp = path.stat().st_mtime_ns
    path.write_text('value=2\n')
    os.utime(path, ns=(stamp, stamp))
    changed = graph(tmp_path).fingerprint
    assert before != changed
    put(tmp_path, 'added.py', 'x=1\n')
    assert graph(tmp_path).fingerprint != changed
    path.rename(tmp_path / 'renamed.py')
    value = graph(tmp_path)
    assert 'file:session.py' not in value.nodes
    assert 'file:renamed.py' in value.nodes
    (tmp_path / 'added.py').unlink()
    assert graph(tmp_path).fingerprint != value.fingerprint


def test_scan_and_file_read_limits_are_visible(tmp_path):
    put(tmp_path, 'a.py', 'x=1\n')
    put(tmp_path, 'b.py', 'x=2\n')
    assert graph(tmp_path, max_files=2).coverage['complete']
    assert not graph(tmp_path, max_files=1).coverage['complete']
    assert not graph(tmp_path, max_bytes=3).coverage['complete']
    assert not graph(tmp_path, seconds=0).coverage['complete']
    put(tmp_path, 'big.py', '#' * (4 * 1024 * 1024 + 1))
    assert 'per-file' in ' '.join(graph(tmp_path).issues)


def test_ignored_generated_and_nested_repository_are_excluded(tmp_path):
    def git(root, *args):
        subprocess.run(['git', '-c', f'safe.directory={root.as_posix()}', *args],
                       cwd=root, check=True, capture_output=True)
    git(tmp_path, 'init', '-q')
    put(tmp_path, '.gitignore', 'generated/\n')
    put(tmp_path, 'generated/noise.py', 'raise Exception()\n')
    put(tmp_path, 'app.py', 'x=1\n')
    child = tmp_path / 'other'
    child.mkdir()
    git(child, 'init', '-q')
    put(child, 'private.py', 'x=1\n')
    assert set(graph(tmp_path).nodes) == {'file:app.py'}


def test_non_git_and_subdirectory_scopes_work(tmp_path):
    put(tmp_path, 'outer.py', 'x=1\n')
    child = tmp_path / 'child'
    child.mkdir()
    put(child, 'inner.py', 'x=1\n')
    assert set(graph(child).nodes) == {'file:inner.py'}


def test_invalid_root_and_nonfinite_deadline_rejected(tmp_path):
    with pytest.raises(ValueError):
        graph(tmp_path / 'missing')
    with pytest.raises(ValueError):
        graph(tmp_path, seconds=float('nan'))


def test_symlink_input_is_never_parsed(tmp_path):
    outside = put(tmp_path, 'secret.py', 'def secret(): pass\n')
    project = tmp_path / 'project'
    project.mkdir()
    try:
        (project / 'link.py').symlink_to(outside)
    except OSError:
        pytest.skip('symlink privilege unavailable')
    value = graph(project)
    assert not value.nodes
    assert value.issues
