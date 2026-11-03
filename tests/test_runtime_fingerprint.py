"""Declared checks ask for the runtime fingerprint before and after each step, seven times
in one `ep_check --all`. It stays a content identity, without re-reading an unchanged
runtime each time.

Known limit, as in Git's index: a same-size edit whose old mtime is put back by hand,
on a file older than two seconds when it was last read, is not seen."""
import os
from pathlib import Path
import shutil
import time

import pytest

SOURCE = Path(__file__).resolve().parents[1]


@pytest.fixture
def runtime(tmp_path):
    root = tmp_path / 'runtime'
    for part in ('core', 'plugin/bin'):
        shutil.copytree(SOURCE / part, root / part, ignore=shutil.ignore_patterns('__pycache__'))
    old = time.time() - 60
    for path in root.rglob('*'):
        if path.is_file():
            os.utime(path, (old, old))
    return root


def _same_size_edit(path):
    data = path.read_bytes()
    path.write_bytes(data.replace(b'def ', b'def_', 1))


def test_an_unchanged_runtime_is_not_read_again(runtime, monkeypatch):
    from core.hosts.provenance import fingerprint
    first = fingerprint(runtime)
    opened, real = [], Path.open
    monkeypatch.setattr(Path, 'open', lambda self, *a, **k: opened.append(self) or real(self, *a, **k))
    assert fingerprint(runtime) == first
    assert opened == []


def test_an_edit_to_a_runtime_file_moves_it(runtime):
    from core.hosts.provenance import fingerprint
    first = fingerprint(runtime)
    _same_size_edit(runtime / 'core/hook.py')
    assert fingerprint(runtime) != first


def test_a_resized_file_moves_it_even_with_its_old_mtime_put_back(runtime):
    from core.hosts.provenance import fingerprint
    first = fingerprint(runtime)
    target = runtime / 'core/hook.py'
    stat = target.stat()
    target.write_bytes(target.read_bytes() + b'\n')
    os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert fingerprint(runtime) != first


def test_a_renamed_file_moves_it(runtime):
    # A rename keeps size and mtime; only the name can tell.
    from core.hosts.provenance import fingerprint
    first = fingerprint(runtime)
    (runtime / 'core/hook.py').rename(runtime / 'core/hook_renamed.py')
    assert fingerprint(runtime) != first


def test_a_file_written_just_before_it_was_read_is_read_again(runtime):
    # Git's racily-clean rule: an mtime that close to the read cannot vouch for the content.
    from core.hosts.provenance import fingerprint
    target = runtime / 'core/hook.py'
    target.write_bytes(target.read_bytes())
    first = fingerprint(runtime)
    stat = target.stat()
    _same_size_edit(target)
    os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert fingerprint(runtime) != first
