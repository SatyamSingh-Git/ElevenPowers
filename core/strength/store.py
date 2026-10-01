"""Atomic saved observations; never store mutant source or command output."""
import json
import os
from pathlib import Path
import tempfile
from .. import jobs
from ..redact import scrub_values
from .model import Observation, summary

MAX_BYTES = 512 * 1024
FIELDS = {'schema_version', 'task', 'state', 'issues', 'observations', 'fingerprint',
          'source_fingerprint', 'baseline', 'engine_versions', 'base', 'command',
          'settings', 'paths', 'recorded_at', 'summary', 'attempts', 'limitations'}
STATES = {'running', 'complete', 'incomplete', 'deferred', 'unavailable', 'not_applicable', 'disabled'}


def validate(value):
    if not isinstance(value, dict) or set(value) != FIELDS or value['schema_version'] != 1:
        raise ValueError('unsupported strength record')
    if value['state'] not in STATES or not isinstance(value['observations'], list) or len(value['observations']) > 256:
        raise ValueError('invalid strength state or observation count')
    items = [Observation(**item) for item in value['observations']]
    value = dict(value)
    value['summary'] = summary(items)
    return value


def path(root):
    folder = root / '.elevenpowers'
    if folder.is_symlink() or getattr(folder, 'is_junction', lambda: False)():
        raise ValueError('linked strength state directory is unsafe')
    return folder / 'strength.json'


def save(root, value):
    value = validate(scrub_values(value))
    content = json.dumps(value, ensure_ascii=True, allow_nan=False)
    if len(content.encode('utf-8')) > MAX_BYTES:
        raise ValueError('strength record exceeds metadata limit')
    target = path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    with jobs.ledger_write(root):
        name = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent,
                                             prefix='.strength-', delete=False) as stream:
                name = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            jobs.replace(name, target)
        finally:
            if name is not None:
                name.unlink(missing_ok=True)


def load(root, task):
    try:
        target = path(root)
        if not target.exists():
            return None
        if target.is_symlink() or target.stat().st_size > MAX_BYTES:
            raise ValueError('unsafe or oversized strength record')
        value = validate(json.loads(target.read_text(encoding='utf-8')))
        return value if value['task'] == task else None
    except (OSError, ValueError, TypeError, KeyError):
        return {'state': 'incomplete', 'task': task, 'issues': ['saved strength record is unreadable or invalid'],
                'observations': [], 'summary': {}, 'limitations': []}
