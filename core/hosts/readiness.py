"""Bounded callback diagnostics. An observed callback is not host authentication."""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
import time
import uuid

from ..jobs import ledger_write
from ..ledger import _keep_out_of_git

SOURCE = ContextVar('callback_ingress', default=None)


@contextmanager
def ingress(source):
    token = SOURCE.set(source)
    try:
        yield
    finally:
        SOURCE.reset(token)


@contextmanager
def state(root):
    from .setup import _write
    root = Path(root).resolve(strict=True)
    directory = root / '.elevenpowers'
    if not directory.resolve().is_relative_to(root):
        raise ValueError('integration state escapes project root')
    directory.mkdir(exist_ok=True)
    _keep_out_of_git(directory)
    path = directory / 'integrations.json'
    with ledger_write(root):
        value = read(root)
        yield value
        _write(path, value)


def read(root):
    path = Path(root) / '.elevenpowers/integrations.json'
    value = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if not isinstance(value, dict) or any(not isinstance(v, dict) for v in value.values()):
        raise ValueError('invalid integration state')
    return value


def signature(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ''


def configured(platform, root, path, changed=False):
    with state(root) as value:
        previous = value.get(platform, {})
        if changed or previous.get('state') == 'removed' or not previous.get('configuration'):
            previous = {'state': 'waiting', 'generation': uuid.uuid4().hex,
                        'configured_at': time.time(), 'received': 0, 'processed': 0}
        previous['configuration'] = signature(path)
        value[platform] = previous


def removed(platform, root):
    with state(root) as value:
        value[platform] = {'state': 'removed', 'generation': uuid.uuid4().hex}


def activation(platform, root):
    from .setup import config_path
    value = dict(read(root).get(platform, {'state': 'unobserved'}))
    if value.get('configuration') and signature(config_path(platform, root)) != value['configuration']:
        value['state'] = 'configuration-changed'
    return value


@contextmanager
def callback(platform, root, event):
    if SOURCE.get() != 'host':
        yield
        return
    with state(root) as value:
        item = value.setdefault(platform, {'state': 'received', 'generation': uuid.uuid4().hex})
        generation = item['generation']
        item.update(last_event=event, received_at=time.time(),
                    received=min(item.get('received', 0) + 1, 1_000_000_000))
    error = None
    try:
        yield
    except BaseException as exc:
        error = type(exc).__name__
        raise
    finally:
        with state(root) as value:
            item = value.get(platform, {})
            if item.get('generation') == generation:
                if error:
                    item.update(state='error', error=error)
                else:
                    item.pop('error', None)
                    item.update(processed_at=time.time(), processed=min(item.get('processed', 0) + 1, 1_000_000_000))
                    if event == 'SessionStart':
                        item['startup_processed_at'] = time.time()
                    item['state'] = 'active' if item.get('startup_processed_at') else 'received'
