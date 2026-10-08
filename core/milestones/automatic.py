"""Bounded optional advice; reservations are diagnostic state, never evidence."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
import uuid

from ..jobs import Busy, ledger_write
from ..ledger import Ledger, _keep_out_of_git
from ..hosts.setup import _write
from ..process import run
from .advice import policy
from .definition import configured, safe_path

TOOL_ROOT = Path(__file__).resolve().parents[2]
HEX = frozenset('0123456789abcdef')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def signature(ledger):
    # Metadata is only a work-deduplication hint, never a freshness witness.
    paths = sorted(set(ledger.touched))[:256]
    items = []
    for name in [*paths, 'elevenpowers.milestones.json', 'impactgraph.json']:
        try:
            stat = safe_path(ledger.root, name).stat()
            items.append([name, stat.st_mtime_ns, stat.st_size])
        except (OSError, ValueError):
            items.append([name, None])
    return digest([ledger.task, items, len(ledger.touched), vars(ledger.config),
                   [(e.kind.value, e.command, e.at) for e in ledger.evidence[-128:]]])


def _read(path):
    if not path.exists():
        return {'schema': 1, 'tasks': []}
    with path.open('rb') as stream:
        data = stream.read(65537)
    if len(data) > 65536:
        raise ValueError('advice state exceeds 64 KiB')
    value = json.loads(data)
    if (not isinstance(value, dict) or value.get('schema') != 1
            or not isinstance(value.get('tasks'), list) or len(value['tasks']) > 20):
        raise ValueError('invalid advisory state')
    if type(value.get('evicted_tasks', 0)) is not int or not 0 <= value.get('evicted_tasks', 0) <= 10**9:
        raise ValueError('invalid advisory eviction count')
    for task in value['tasks']:
        if (not isinstance(task, dict) or not _hash(task.get('id'))
                or not isinstance(task.get('attempts'), list) or len(task['attempts']) > 10):
            raise ValueError('invalid advisory task')
        for attempt in task['attempts']:
            if (not isinstance(attempt, dict) or not _hash(attempt.get('key'))
                    or not isinstance(attempt.get('id'), str)
                    or attempt.get('status') not in {'reserved', 'delivered', 'incomplete'}
                    or type(attempt.get('at')) not in (int, float)
                    or not 0 <= attempt['at'] <= 10**12):
                raise ValueError('invalid advisory attempt')
            if 'context' in attempt and not _hash(attempt['context']):
                raise ValueError('invalid advisory context hash')
            checks = attempt.get('checks', [])
            if not isinstance(checks, list) or len(checks) > 6 or any(not _hash(c) for c in checks):
                raise ValueError('invalid advisory check hashes')
            if 'emission' in attempt:
                emission = attempt['emission']
                from ..hosts.setup import PATHS
                if (not isinstance(emission, dict) or
                        set(emission) != {'host', 'generation', 'session', 'runtime', 'context', 'at'} or
                        emission['host'] not in PATHS or
                        not isinstance(emission['generation'], str) or
                        len(emission['generation']) != 32 or set(emission['generation']) - HEX or
                        any(not _hash(emission[k]) for k in ('session', 'runtime', 'context')) or
                        emission['context'] != attempt.get('context') or
                        type(emission['at']) not in (int, float) or not math.isfinite(emission['at']) or
                        not attempt['at'] <= emission['at'] <= 10**12):
                    raise ValueError('invalid advisory emission')
    return value


def _hash(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX


def _paths(root):
    state = root / '.elevenpowers'
    if state.is_symlink() or not state.resolve().is_relative_to(root.resolve()):
        raise ValueError('linked advisory state')
    state.mkdir(exist_ok=True)
    _keep_out_of_git(state)
    path = state / 'advice.json'
    if path.is_symlink() or (state / 'ledger.lock').is_symlink():
        raise ValueError('linked advisory state file')
    return path


def _store(path, value, *, keep_task=None):
    # Metadata grows with optional emission observations. Retain newest task
    # allowances, and keep every writer within the reader's existing limit.
    while len((json.dumps(value, indent=2) + '\n').encode('utf8')) > 65536:
        if len(value['tasks']) <= 1:
            raise ValueError('current advisory task exceeds state byte limit')
        remove = next((i for i, task in enumerate(value['tasks']) if task['id'] != keep_task), None)
        if remove is None:
            raise ValueError('protected advisory task exceeds state byte limit')
        value['tasks'].pop(remove)
        value['evicted_tasks'] = min(10**9, value.get('evicted_tasks', 0) + 1)
    _write(path, value)


def _reserve(root, task_id, key, settings):
    path = _paths(root)
    with ledger_write(root, timeout=.05):
        value = _read(path)
        task = next((t for t in value['tasks'] if t['id'] == task_id), None)
        if task is None:
            task = {'id': task_id, 'attempts': []}
            if len(value['tasks']) >= 20:
                value['evicted_tasks'] = min(10**9, value.get('evicted_tasks', 0) + 1)
            value['tasks'] = [*value['tasks'][-19:], task]
        attempts = task['attempts']
        now = time.time()
        if (len(attempts) >= settings['max_attempts']
                or any(a['key'] == key for a in attempts)
                or attempts and now - attempts[-1]['at'] < settings['cooldown']):
            return None
        identity = uuid.uuid4().hex
        attempts.append({'id': identity, 'key': key, 'at': now, 'status': 'reserved'})
        _store(path, value, keep_task=task_id)
        return identity


def _finish(root, task_id, identity, status, elapsed, context='', checks=()):
    path = _paths(root)
    with ledger_write(root, timeout=.05):
        value = _read(path)
        for task in value['tasks']:
            if task['id'] == task_id:
                for attempt in task['attempts']:
                    if attempt['id'] == identity:
                        attempt.update(status=status, elapsed_ms=round(elapsed * 1000, 3))
                        if status == 'delivered':
                            from .delivery import content_hash
                            attempt.update(context=content_hash(context), checks=list(checks))
        _store(path, value, keep_task=task_id)


def deliver(ledger):
    if not ledger.config.speaks or not ledger.task or not ledger.touched or not configured(ledger.root):
        return ''
    started = time.monotonic()
    try:
        settings = policy(ledger.config.milestone_advice)
        if settings is None:
            return ''
        task_id, key = digest(ledger.task), signature(ledger)
        identity = _reserve(ledger.root, task_id, key, settings)
        if identity is None:
            return ''
    except (OSError, ValueError, TypeError, RecursionError, Busy):
        return 'ElevenPowers milestone advice unavailable: resolve invalid configuration or advisory state. Keep fallback verification.'
    status = 'incomplete'
    checks = []
    text = 'ElevenPowers milestone advice incomplete: worker timed out or failed. Keep fallback verification; inspect ep_milestones.py explicitly.'
    try:
        done = run([sys.executable, '-I', str(Path(__file__).with_name('advice_worker.py')),
                    str(ledger.root.resolve()), str(settings['seconds']), task_id],
                   cwd=TOOL_ROOT, shell=False, timeout=settings['seconds'] + .5)
        if done.returncode != 0 or len(done.stdout.encode('utf-8')) > 32768:
            raise ValueError('worker output unavailable')
        value = json.loads(done.stdout)
        if (not isinstance(value, dict) or value.get('schema') != 1
                or not isinstance(value.get('context'), str) or len(value['context']) > 6000):
            raise ValueError('invalid worker context')
        checks = value.get('checks', [])
        if not isinstance(checks, list) or len(checks) > 6 or any(not _hash(c) for c in checks):
            raise ValueError('invalid worker recommendation identities')
        text, status = value['context'], 'delivered'
    except (OSError, ValueError, TypeError, RecursionError, subprocess.SubprocessError):
        pass
    # Check current policy even after worker failure: off suppresses diagnostics
    # as well as successful context. Metadata signatures are dedup hints only.
    try:
        current = Ledger.load(ledger.root)
        if not current.config.speaks or current.task != ledger.task:
            text, status = '', 'incomplete'
        elif signature(current) != key:
            text = 'ElevenPowers milestone advice incomplete: task inputs or configuration changed during inspection. Keep fallback verification.'
            status = 'incomplete'
    except (OSError, ValueError, TypeError, RecursionError):
        text = 'ElevenPowers milestone advice incomplete: current delivery policy unavailable. Keep fallback verification.'
        status = 'incomplete'
    try:
        _finish(ledger.root, task_id, identity, status, time.monotonic() - started, text, checks)
    except (OSError, ValueError, TypeError, RecursionError, Busy):
        return ('ElevenPowers milestone advice incomplete: delivery state unavailable. Keep fallback verification.'
                if text else '')
    if status == 'delivered':
        from .delivery import prepare
        prepare(ledger.root, task_id, identity, text)
    return text
