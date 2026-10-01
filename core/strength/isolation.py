"""Bounded working-copy isolation; dependencies are copied, never aliased."""
from pathlib import Path
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
