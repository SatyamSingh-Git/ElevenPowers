"""Explicit bounded proposal capture. No Git writes or product export changes.

Borrow the checkpoint concept, but read a frozen allowlist rather than staging
the tree. Hash chains detect accidental history edits, not hostile forgery.
"""
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath

MAX_BYTES = 512 * 1024
MAX_RECORDS = 16
MAX_HISTORY = 24 * 1024 * 1024


def _names(names):
    if not isinstance(names, list) or not 1 <= len(names) <= 32 or len(set(names)) != len(names):
        raise ValueError('invalid snapshot allowlist')
    for name in names:
        if (not isinstance(name, str) or '\\' in name or ':' in name or
                not name or name.startswith('.') or
                any(p in ('..', '.') for p in name.split('/')) or
                PurePosixPath(name).is_absolute()):
            raise ValueError('unsafe snapshot path')
    return sorted(names)


def snapshot(root, names):
    names = _names(names)
    root = Path(root).absolute()
    result = {'state': 'incomplete', 'files': {}, 'fingerprint': None}
    if any(p.is_symlink() for p in (root, *root.parents)):
        return result
    total, data, stamps = 0, {}, {}
    try:
        for name in names:
            path = root / name
            if any(p.is_symlink() for p in (path, *path.parents)) or not path.resolve().is_relative_to(root.resolve()):
                return result
            if not path.exists():
                data[name] = None; stamps[name] = None
                continue
            before = path.stat()
            if not path.is_file():
                return result
            with path.open('rb') as stream:
                raw = stream.read(MAX_BYTES - total + 1)
            total += len(raw)
            if total > MAX_BYTES or path.stat() != before:
                return result
            stamps[name] = before
            data[name] = base64.b64encode(raw).decode('ascii')
        for name, stamp in stamps.items():
            path = root / name
            if (stamp is None and path.exists()) or (stamp is not None and path.stat() != stamp):
                return result
    except OSError:
        return result
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    return {'state': 'complete', 'files': data, 'fingerprint': digest}


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def read(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('linked history')
    if not path.exists():
        return []
    with path.open('rb') as stream:
        raw = stream.read(MAX_HISTORY + 1)
    if len(raw) > MAX_HISTORY:
        raise ValueError('history exceeds limit')
    values, previous = [], '0' * 64
    try:
        for line in raw.splitlines():
            value = json.loads(line)
            digest = value.pop('hash')
            if value['previous'] != previous or digest != _hash(value) or len(values) >= MAX_RECORDS + 1:
                raise ValueError('invalid history chain')
            value['hash'] = digest
            values.append(value); previous = digest
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('invalid proposal history') from error
    return values


def append(path, value):
    path = Path(path)
    history = read(path)
    if len(history) > MAX_RECORDS:
        return
    if len(history) == MAX_RECORDS:
        value = {'state': 'overflow'}
    record = {**value, 'previous': history[-1]['hash'] if history else '0' * 64}
    record['hash'] = _hash(record)
    encoded = json.dumps(record, allow_nan=False) + '\n'
    if path.exists() and path.stat().st_size + len(encoded.encode()) > MAX_HISTORY:
        raise ValueError('history exceeds limit')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as stream:
        stream.write(encoded)
