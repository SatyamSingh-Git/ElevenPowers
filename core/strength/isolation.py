"""Bounded working-copy isolation; dependencies are copied, never aliased."""
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import tempfile
import time
from .model import relative
from .scope import git


def safe_file(root, path):
    relative(path)
    item = root / path
    for parent in (item, *item.parents):
        if parent == root:
            break
        if parent.is_symlink() or getattr(parent, 'is_junction', lambda: False)():
            raise ValueError('linked input cannot be isolated: ' + path)
        if parent.is_dir() and (parent / '.git').exists():
            raise ValueError('nested repository cannot be isolated: ' + path)
    if not item.is_file() or not item.resolve().is_relative_to(root.resolve()):
        raise ValueError('unavailable or unsafe isolation input: ' + path)
    return item


def copy_plan(root, settings, deadline):
    paths = set(git(root, ['ls-files', '-z', '--cached', '--others', '--exclude-standard'], deadline).split('\0')) - {''}
    paths = {p for p in paths if not any(part in ('.git', '.elevenpowers', '__pycache__')
                                       for part in Path(p).parts)}
    # The index still names files deleted in the current working tree. A copy
    # represents current inputs, so carry their absence rather than restoring base.
    paths = {p for p in paths if (root / p).exists() or (root / p).is_symlink()}
    dependencies = list(settings.dependencies)
    # A conventional installed JS dependency tree is needed by ordinary tests.
    # Copy it under the same limits; linking would let tests mutate the original.
    if (root / 'node_modules').exists() and 'node_modules' not in dependencies:
        dependencies.append('node_modules')
    for dependency in dependencies:
        relative(dependency)
        item = root / dependency
        if item.is_symlink() or getattr(item, 'is_junction', lambda: False)():
            raise ValueError('linked dependency cannot be isolated: ' + dependency)
        if not item.exists():
            raise ValueError('declared dependency is unavailable: ' + dependency)
        if item.is_file():
            paths.add(dependency)
        else:
            import os
            for directory, folders, files in os.walk(item, followlinks=False):
                if time.monotonic() >= deadline:
                    raise TimeoutError('strength deadline reached selecting dependencies')
                here = Path(directory)
                for folder in folders:
                    entry = here / folder
                    if entry.is_symlink() or getattr(entry, 'is_junction', lambda: False)() or (entry / '.git').exists():
                        raise ValueError('linked or nested dependency cannot be isolated')
                paths.update((here / file).relative_to(root).as_posix() for file in files)
                if len(paths) > settings.max_files:
                    raise ValueError('isolation file limit exceeded')
    if len(paths) > settings.max_files:
        raise ValueError('isolation file limit exceeded')
    size = 0
    for path in sorted(paths):
        if time.monotonic() >= deadline:
            raise TimeoutError('strength deadline reached selecting inputs')
        size += safe_file(root, path).stat().st_size
        if size > settings.max_bytes:
            raise ValueError('isolation byte limit exceeded')
    return sorted(paths)


def fingerprint(root, paths, settings, deadline, *, destination=None):
    digest = hashlib.sha256()
    total = 0
    for path in paths:
        if time.monotonic() >= deadline:
            raise TimeoutError('strength deadline reached reading inputs')
        source = safe_file(root, path)
        file_hash = hashlib.sha256()
        target = None
        try:
            if destination is not None:
                output = destination / path
                output.parent.mkdir(parents=True, exist_ok=True)
                target = output.open('xb')
            with source.open('rb') as stream:
                while chunk := stream.read(1024 * 1024):
                    total += len(chunk)
                    if total > settings.max_bytes:
                        raise ValueError('isolation byte limit exceeded during copy')
                    if time.monotonic() >= deadline:
                        raise TimeoutError('strength deadline reached copying inputs')
                    file_hash.update(chunk)
                    if target:
                        target.write(chunk)
            if target:
                target.close()
                target = None
                output.chmod(source.stat().st_mode & 0o777)
            safe_file(root, path)
        finally:
            if target:
                target.close()
        digest.update(path.encode('utf-8') + b'\0' + file_hash.digest())
    return digest.hexdigest()


@dataclass(frozen=True)
class Snapshot:
    root: Path
    paths: list[str]
    stamp: str


@contextmanager
def snapshot(root, settings, deadline):
    paths = copy_plan(root, settings, deadline)
    with tempfile.TemporaryDirectory(prefix='ep-strength-') as directory:
        copied = Path(directory)
        stamp = fingerprint(root, paths, settings, deadline, destination=copied)
        if stamp != fingerprint(root, paths, settings, deadline):
            raise ValueError('inputs changed while creating isolated snapshot')
        yield Snapshot(copied, paths, stamp)


@contextmanager
def trial(pristine, settings, deadline):
    """Each test invocation starts from identical inputs, including secondary files."""
    with tempfile.TemporaryDirectory(prefix='ep-strength-trial-') as directory:
        copied = Path(directory)
        stamp = fingerprint(pristine.root, pristine.paths, settings, deadline, destination=copied)
        if stamp != pristine.stamp:
            raise ValueError('pristine analysis inputs changed')
        yield copied
