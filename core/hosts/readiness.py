"""Bounded callback diagnostics. An observed callback is not host authentication."""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
import time
import uuid
from .diagnostics import PHASES, read_json, validate

from ..jobs import ledger_write
from ..ledger import _keep_out_of_git

SOURCE = ContextVar('callback_ingress', default=None)
_OBSERVATION = ContextVar('native_health_observation', default=None)


def identity(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest() if isinstance(value, str) and value else ''


def receipt_key(record):
    data = record if isinstance(record, dict) else record.to_dict()
    return identity(json.dumps([data['kind'], data['identity'], data['command'],
                               data.get('recorded_at', data.get('at', 0))], sort_keys=True))


def record_task(task):
    observation = _OBSERVATION.get()
    if observation is not None:
        observation['task'] = identity(task)


def record_receipts(records, task):
    observation = _OBSERVATION.get()
    if observation is not None:
        record_task(task)
        for r in records:
            if r.declaration:
                observation['links'].append({'key': receipt_key(r), 'result': r.result.value, 'execution': r.execution})
                if len(observation['links']) > 64:
                    observation['links'].pop(0)
                    observation['evicted'] += 1


def record_edit(task, changed, incomplete=False):
    observation = _OBSERVATION.get()
    if observation is not None:
        record_task(task)
        observation['edit'] = {'changed': changed, 'incomplete': incomplete}


def emission_scope():
    observation = _OBSERVATION.get()
    if SOURCE.get() != 'host' or observation is None:
        return None
    return {key: observation[key] for key in ('host', 'generation', 'session')}


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
    return validate(read_json(path))


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
def callback(platform, root, event, payload=None):
    if SOURCE.get() != 'host':
        yield
        return
    from .setup import PATHS
    if platform not in PATHS:
        raise ValueError('unsupported callback platform')
    if event not in PHASES:
        raise ValueError('unsupported callback phase')
    session = identity((payload or {}).get('session_id'))
    started = time.monotonic()
    runtime = ''
    if event == 'SessionStart':
        from .provenance import fingerprint
        try:
            runtime = fingerprint()
        except (OSError, ValueError):
            # Missing identity cannot qualify a runtime-bound acceptance read.
            runtime = ''
    with state(root) as value:
        item = value.setdefault(platform, {'state': 'received', 'generation': uuid.uuid4().hex})
        generation = item['generation']
        item.update(last_event=event, received_at=time.time(),
                    received=min(item.get('received', 0) + 1, 1_000_000_000))
        phase = item.setdefault('phases', {}).setdefault(event, {})
        phase.update(received=min(phase.get('received', 0) + 1, 1_000_000_000))
    observation = {'links': [], 'task': '', 'session': session, 'evicted': 0,
                   'host': platform, 'generation': generation}
    token = _OBSERVATION.set(observation)
    error = None
    try:
        yield
    except BaseException as exc:
        error = type(exc).__name__
        raise
    finally:
        elapsed = max(0, (time.monotonic() - started) * 1000)
        _OBSERVATION.reset(token)
        with state(root) as value:
            item = value.get(platform, {})
            if item.get('generation') == generation:
                phase = item.setdefault('phases', {}).setdefault(event, {})
                phase.update(task=observation['task'], session=session, last_at=time.time())
                if event == 'SessionStart':
                    phase['runtime_fingerprint'] = runtime
                if 'edit' in observation:
                    phase['edit'] = {**observation['edit'], 'task': observation['task'], 'session': session}
                phase['samples_ms'] = [*phase.get('samples_ms', [])[-31:], round(elapsed, 3)]
                if error:
                    phase.update(errors=min(phase.get('errors', 0) + 1, 1_000_000_000), last_error=error)
                    item.update(state='error', error=error, last_error=error, error_at=time.time(),
                                errors=min(item.get('errors', 0) + 1, 1_000_000_000))
                else:
                    phase.pop('last_error', None)
                    phase['processed'] = min(phase.get('processed', 0) + 1, 1_000_000_000)
                    links = item.get('receipt_links', []) + [
                        {**link, 'task': observation['task'], 'session': session, 'at': time.time()}
                        for link in observation['links']]
                    item['links_evicted'] = min(1_000_000_000, item.get('links_evicted', 0) + max(0, len(links) - 64) + observation['evicted'])
                    item['receipt_links'] = links[-64:]
                    item.pop('error', None)
                    item.update(processed_at=time.time(), processed=min(item.get('processed', 0) + 1, 1_000_000_000))
                    if event == 'SessionStart':
                        item['startup_processed_at'] = time.time()
                    item['state'] = 'active' if item.get('startup_processed_at') else 'received'
