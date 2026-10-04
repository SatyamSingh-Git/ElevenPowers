"""Graph controls distinguish actual relationships from name resemblance."""
import os
import subprocess
import time

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
    put(tmp_path, 'session.py', 'def expire(): pass\n')
    put(tmp_path, 'src/session.py', 'def expire(): pass\n')
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


@pytest.mark.parametrize('source', [
    'from session import expire\ndef use(v):\n    match v:\n        case {"handler": expire}:\n            return expire()\n',
    'import session\nsession.expire = lambda: 2\nsession.expire()\n',
    'import session\nsetattr(session, "expire", lambda: 2)\nsession.expire()\n',
])
def test_match_and_module_mutation_do_not_invent_imported_calls(tmp_path, source):
    put(tmp_path, 'session.py', 'def expire(): return 1\n')
    put(tmp_path, 'api.py', source)
    value = graph(tmp_path)
    assert ('file:api.py', 'symbol:session.py#expire') not in links(value, 'calls')
    assert value.issues


def test_large_binding_resolution_obeys_cooperative_deadline(tmp_path):
    put(tmp_path, 'session.py', 'def expire(): return 1\n')
    names = [f'expire as n{i}' for i in range(6000)]
    put(tmp_path, 'api.py', 'from session import ' + ','.join(names) + '\n' +
        '\n'.join('n5999()' for i in range(6000)))
    started = time.monotonic()
    value = graph(tmp_path, seconds=.4)
    assert time.monotonic() - started < 2.5
    assert value.coverage['complete'] or 'deadline' in ' '.join(value.issues)


@pytest.mark.parametrize('files,source,target', [
    ({'pkg/__init__.py': 'def session(): return 1\n', 'pkg/session.py': 'x=1\n'},
     'from pkg import session\nsession()\n', 'symbol:pkg/__init__.py#session'),
    ({'pkg/__init__.py': '', 'pkg/session.py': 'def expire(): return 1\n'},
     'import pkg\nimport pkg.session\npkg.session.expire()\n', 'symbol:pkg/session.py#expire'),
])
def test_initializer_exports_and_longest_module_binding(tmp_path, files, source, target):
    for path, code in files.items():
        put(tmp_path, path, code)
    put(tmp_path, 'api.py', source)
    assert ('file:api.py', target) in links(graph(tmp_path), 'calls')


@pytest.mark.parametrize('files,source', [
    ({'examples/session.py': 'def expire(): pass\n'}, 'from session import expire\nexpire()\n'),
    ({'pkg/api.py': 'from ...session import expire\nexpire()\n', 'expire.py': 'x=1\n'}, None),
    ({'session.py': 'def expire(): pass\nexpire = lambda: 2\n'}, 'from session import expire\nexpire()\n'),
])
def test_unavailable_module_roots_and_rebound_exports_are_not_resolved(tmp_path, files, source):
    for path, code in files.items():
        put(tmp_path, path, code)
    if source:
        put(tmp_path, 'api.py', source)
    value = graph(tmp_path)
    assert not links(value, 'calls')
    assert value.issues


def test_bounded_scan_does_not_discover_commands_from_large_manifest(tmp_path, monkeypatch):
    path = put(tmp_path, 'package.json', ' ' * (5 * 1024 * 1024))
    original = type(path).read_text
    def read_text(file, *args, **kwargs):
        if file == path:
            pytest.fail('manifest read bypassed ImpactGraph byte cap')
        return original(file, *args, **kwargs)
    monkeypatch.setattr(type(path), 'read_text', read_text)
    assert 'per-file' in ' '.join(graph(tmp_path).issues)


def test_scanning_disables_project_filesystem_monitor(tmp_path):
    git = ['git', '-c', f'safe.directory={tmp_path.as_posix()}']
    subprocess.run([*git, 'init', '-q'], cwd=tmp_path, check=True, capture_output=True)
    put(tmp_path, 'app.py', 'x=1\n')
    subprocess.run([*git, 'add', '.'], cwd=tmp_path, check=True, capture_output=True)
    script = put(tmp_path, 'monitor.sh', '#!/bin/sh\ntouch monitor-ran.txt\nprintf "token\\0"\n')
    script.chmod(0o755)
    subprocess.run([*git, 'config', 'core.fsmonitor', script.as_posix()], cwd=tmp_path, check=True)
    graph(tmp_path)
    assert not (tmp_path / 'monitor-ran.txt').exists()


def test_class_attribute_initialization_does_not_rebind_the_class_export(tmp_path):
    put(tmp_path, 'api.py', 'class Api: pass\nApi.template_type = object\n')
    put(tmp_path, 'client.py', 'from api import Api\ndef client(): return Api()\n')
    value = graph(tmp_path)
    assert 'symbol:api.py#Api' in value.nodes
    assert ('file:client.py', 'symbol:api.py#Api') in links(value, 'calls')


def test_function_implementation_mutation_still_cannot_supply_a_qualified_export(tmp_path):
    put(tmp_path, 'api.py', 'def expire(): return 1\ndef replacement(): return 2\n'
        'expire.__code__ = replacement.__code__\n')
    put(tmp_path, 'client.py', 'from api import expire\nexpire()\n')
    value = graph(tmp_path)
    assert 'symbol:api.py#expire' not in value.nodes
    assert ('file:client.py', 'symbol:api.py#expire') not in links(value, 'calls')
