"""Bounded content identity of this runtime, independent of checkout path."""
import hashlib
import os
from pathlib import Path

MAX_FILES = 512
MAX_BYTES = 8 * 1024 * 1024


def fingerprint(source=None):
    root = Path(source or Path(__file__).resolve().parents[2]).resolve(strict=True)
    files = []
    for directory in (root / 'core', root / 'plugin/bin'):
        if not directory.is_dir():
            raise ValueError('runtime source directories unavailable')
        for base, folders, names in os.walk(directory, followlinks=False):
            folders[:] = [name for name in folders if name != '__pycache__']
            for name in folders:
                path = Path(base) / name
                if path.is_symlink() or path.resolve() != path.absolute():
                    raise ValueError('linked runtime directory')
            for name in names:
                path = Path(base) / name
                if path.suffix not in ('.py', '.mjs'):
                    continue
                if path.is_symlink() or path.resolve() != path.absolute():
                    raise ValueError('linked runtime file')
                files.append(path)
                if len(files) > MAX_FILES:
                    raise ValueError('runtime file limit reached')
    if not files:
        raise ValueError('runtime source files unavailable')
    digest, total = hashlib.sha256(), 0
    for path in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
        with path.open('rb') as stream:
            data = stream.read(MAX_BYTES - total + 1)
        total += len(data)
        if total > MAX_BYTES:
            raise ValueError('runtime byte limit reached')
        name = path.relative_to(root).as_posix().encode('utf-8')
        digest.update(len(name).to_bytes(4, 'big') + name)
        digest.update(len(data).to_bytes(8, 'big') + data)
    return digest.hexdigest()
