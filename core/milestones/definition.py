"""Strict, bounded project declarations; parsing never executes a check."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import time

FILE = 'elevenpowers.milestones.json'
MAX_BYTES = 128 * 1024
KINDS = {'test_suite', 'build', 'typecheck', 'lint', 'benchmark'}


def safe_path(root, value):
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError('input must be a nonempty normalized relative path')
    path = PurePosixPath(value)
    if ('\\' in value or ':' in value or path.is_absolute() or str(path) != value
            or '..' in path.parts or any(p in {'.git', '.elevenpowers'} for p in path.parts)):
        raise ValueError('unsafe milestone input path')
    root = Path(root).resolve()
    full = root / value
    if (any((root / str(p)).is_symlink() for p in (path, *path.parents))
            or any((root / str(p) / '.git').exists() for p in path.parents if str(p) != '.')
            or not full.resolve().is_relative_to(root)):
        raise ValueError('linked or nested-repository milestone input')
    if full.exists() and not full.is_file():
        raise ValueError('milestone input must be an ordinary file')
    return full


def configured(root):
    path = Path(root) / FILE
    return path.exists() or path.is_symlink()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field in milestone declaration')
        result[key] = value
    return result


def _text(value, name, maximum=4096):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'invalid milestone {name}')


def _array(value, name, maximum):
    if not isinstance(value, list) or not 1 <= len(value) <= maximum:
        raise ValueError(f'invalid milestone {name} count (1-{maximum})')


def load(root, *, deadline=None):
    result = {'configured': configured(root), 'fingerprint': '', 'milestones': [], 'issues': []}
    if not result['configured']:
        return result
    try:
        if deadline is not None and time.monotonic() >= deadline:
            raise ValueError('milestone declaration deadline reached')
        path = safe_path(root, FILE)
        with path.open('rb') as stream:
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('milestone declaration exceeds 128 KiB')
        result['fingerprint'] = hashlib.sha256(data).hexdigest()
        value = json.loads(data.decode('utf-8'), object_pairs_hook=_pairs)
        if (not isinstance(value, dict) or set(value) != {'schema', 'milestones'}
                or type(value['schema']) is not int or value['schema'] != 1):
            raise ValueError('expected milestone declaration schema 1 with no unknown fields')
        _array(value['milestones'], 'definitions', 64)
        ids = set()
        for item in value['milestones']:
            if not isinstance(item, dict) or set(item) != {'id', 'description', 'inputs', 'checks'}:
                raise ValueError('invalid milestone fields')
            _text(item['id'], 'id', 64)
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', item['id']) or item['id'] in ids:
                raise ValueError('invalid or duplicate milestone id')
            ids.add(item['id'])
            _text(item['description'], 'description')
            _array(item['inputs'], 'inputs', 128)
            for name in item['inputs']:
                safe_path(root, name)
            if len(set(item['inputs'])) != len(item['inputs']):
                raise ValueError('duplicate milestone input')
            _array(item['checks'], 'checks', 16)
            checks = set()
            for check in item['checks']:
                if (not isinstance(check, dict) or set(check) != {'kind', 'command'}
                        or not isinstance(check['kind'], str) or check['kind'] not in KINDS):
                    raise ValueError('invalid aggregate milestone check')
                _text(check['command'], 'command')
                if check['command'] != check['command'].strip():
                    raise ValueError('check command must preserve a normalized exact identity')
                key = check['kind'], check['command']
                if key in checks:
                    raise ValueError('duplicate milestone check')
                checks.add(key)
        result['milestones'] = value['milestones']
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError) as error:
        result['issues'].append(f'{type(error).__name__}: milestone declarations unavailable or invalid: {error}')
    return result
