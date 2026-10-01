"""Atomic saved observations; never store mutant source or command output."""
import json
import math
import os
from pathlib import Path
import tempfile
from .. import jobs
from ..redact import scrub_values
from .model import Observation, relative, summary
from .settings import settings

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
    for key in ('task', 'fingerprint', 'source_fingerprint', 'base', 'command', 'baseline'):
        if not isinstance(value[key], str) or len(value[key]) > (8192 if key == 'command' else 256):
            raise ValueError('invalid strength metadata: ' + key)
    if value['baseline'] not in ('passed', 'failed', 'incomplete', 'not_run'):
        raise ValueError('invalid baseline state')
    if type(value['attempts']) is not int or not 0 <= value['attempts'] <= 256:
        raise ValueError('invalid strength attempt count')
    if type(value['recorded_at']) not in (int, float) or not math.isfinite(value['recorded_at']) or value['recorded_at'] <= 0:
        raise ValueError('invalid observation timestamp')
    for key in ('issues', 'limitations', 'paths'):
        if not isinstance(value[key], list) or any(not isinstance(item, str) or len(item) > 4096 for item in value[key]):
            raise ValueError('invalid strength metadata list: ' + key)
    for item in value['paths']:
        relative(item)
    settings(value['settings'])
    if not isinstance(value['engine_versions'], dict) or any(
        key not in ('cosmic-ray', 'stryker') or not isinstance(version, str) or len(version) > 32
        for key, version in value['engine_versions'].items()):
        raise ValueError('invalid engine version metadata')
    if value['state'] == 'complete' and (value['baseline'] != 'passed' or value['issues'] or summary(items)['incomplete']):
        raise ValueError('complete analysis needs a passing baseline and complete observations')
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
        from ..ledger import Ledger
        if (root / '.elevenpowers/ledger.json').exists() and Ledger.load(root).task != value['task']:
            raise jobs.Superseded('new task owns the strength observation')
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
