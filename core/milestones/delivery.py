"""Bounded context-emission observations; never evidence of model consumption."""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
from pathlib import Path
import time

from ..hosts import readiness
from ..jobs import Busy, ledger_write

_PENDING = ContextVar('prepared_advice_emissions', default=None)


def content_hash(text):
    return hashlib.sha256(text.encode('utf8')).hexdigest()


def check_hash(kind, command):
    from .automatic import digest
    return digest([kind, command])


@contextmanager
def collect():
    """One launcher's in-memory candidates; nested calls cannot leak scope."""
    token = _PENDING.set([])
    try:
        yield
    finally:
        _PENDING.reset(token)


def prepare(root, task, identity, text):
    pending = _PENDING.get()
    observed = readiness.emission_scope()
    if pending is None or not observed or not observed['session'] or not text:
        return
    from ..hosts.provenance import fingerprint
    try:
        runtime = fingerprint()
    except (OSError, ValueError):
        return
    if len(pending) < 10:
        pending.append({'root': root, 'task': task, 'id': identity, 'text': text,
                        'context': content_hash(text), 'runtime': runtime, **observed})


def _contexts(response):
    # Only documented context slots. Do not search arbitrary response values.
    if not isinstance(response, dict):
        return []
    nodes = [response]
    if isinstance(response.get('hookSpecificOutput'), dict):
        nodes.append(response['hookSpecificOutput'])
    return [node[key] for node in nodes for key in ('additionalContext', 'additional_context')
            if isinstance(node.get(key), str)]


def emitted(response):
    """Call only after successful stdout flush; metadata failure is non-gating."""
    if readiness.SOURCE.get() != 'host':
        return
    pending = _PENDING.get() or []
    contexts = _contexts(response)
    from .automatic import _paths, _read, _store
    for candidate in pending:
        if not any(candidate['text'] in text for text in contexts):
            continue
        root = candidate['root']
        try:
            live = readiness.activation(candidate['host'], root)
            if (live.get('generation') != candidate['generation'] or
                    live.get('state') in {'removed', 'configuration-changed', 'error'}):
                continue
            path = _paths(root)
            with ledger_write(root, timeout=.05):
                value = _read(path)
                for task in value['tasks']:
                    if task['id'] != candidate['task']:
                        continue
                    for attempt in task['attempts']:
                        if (attempt['id'] == candidate['id'] and attempt['status'] == 'delivered'
                                and attempt.get('context') == candidate['context']
                                and 'emission' not in attempt):
                            attempt['emission'] = {k: candidate[k] for k in
                                                   ('host', 'generation', 'session', 'runtime', 'context')}
                            attempt['emission']['at'] = time.time()
                _store(path, value, keep_task=candidate['task'])
        except (OSError, ValueError, TypeError, KeyError, RecursionError, Busy):
            # The output has already been flushed. Never alter its decision.
            continue


LIMITS = [
    'Generated means the worker returned context; emitted means a native launcher flushed it in a supported context field.',
    'A subsequent matching native receipt is a temporal observation, not proof the agent read or used advice.',
    'These local unsigned observations do not authenticate a host or establish improved coding outcomes.',
    'Missing or evicted history stays unobserved; fallback verification must remain available.',
]


def inspect(root, host, task, activation, receipts):
    """Read bounded metadata and join supplied fresh report rows; no execution."""
    from ..config import load
    from .advice import policy
    from .definition import configured
    from .automatic import _read, digest
    value = {'schema': 1, 'state': 'unconfigured', 'attempts': 0, 'generated': 0,
             'emitted': 0, 'matching_native_receipts': 0, 'checks': [], 'issues': [],
             'model_consumption': 'unproven', 'limits': LIMITS}
    root = Path(root).resolve(strict=True)
    try:
        if not configured(root):
            return value
        config = load(root)
        if not config.speaks or policy(config.milestone_advice) is None:
            value['state'] = 'disabled'
            return value
        path = root / '.elevenpowers/advice.json'
        if path.is_symlink() or path.parent.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('linked or escaped advice state')
        saved = _read(path)
        current = next((row for row in saved['tasks'] if row['id'] == digest(task)), None)
        value['state'] = 'waiting'
        if current is None or not current['attempts']:
            if saved.get('evicted_tasks'):
                value['state'] = 'incomplete'
                value['issues'].append('Older advice tasks were evicted; no current-task observation is available.')
            return value
        attempts = current['attempts']
        value['attempts'] = len(attempts)
        value['generated'] = sum(row['status'] == 'delivered' for row in attempts)
        latest = attempts[-1]
        if latest['status'] != 'delivered':
            value['state'] = 'incomplete'
            value['issues'].append('Latest advice attempt is reserved or incomplete.')
            return value
        value['state'] = 'generated'
        emission = latest.get('emission')
        if emission is None or emission['host'] != host:
            return value
        from ..hosts.provenance import fingerprint
        runtime = fingerprint()
        startup = activation.get('phases', {}).get('SessionStart', {})
        session = startup.get('session', '')
        def qualifies(row):
            item = row.get('emission', {})
            return bool(activation.get('state') == 'active' and startup.get('processed') and
                        not startup.get('last_error') and session and
                        item.get('host') == host and item.get('session') == session and
                        item.get('generation') == activation.get('generation') and
                        item.get('runtime') == runtime == startup.get('runtime_fingerprint') and
                        item.get('at', 0) >= startup.get('last_at', 0))
        value['emitted'] = sum(qualifies(row) for row in attempts)
        if not qualifies(latest):
            value['state'] = 'incomplete'
            value['issues'].append('Emission does not match current wiring, runtime and startup session.')
            return value
        value['state'] = 'emitted'
        links = {link['key']: link for link in activation.get('receipt_links', [])
                 if link.get('task') == readiness.identity(task) and link.get('session') == session
                 and link.get('at', 0) > emission['at']}
        for check in latest.get('checks', []):
            candidates = []
            for row in receipts:
                command = row.get('declared_command') or row.get('command', '')
                link = links.get(row.get('receipt_key'))
                if (row.get('declaration') and check_hash(row['kind'], command) == check and link and
                        row['recorded_at'] > emission['at'] and
                        link['result'] == row['result'] and link['execution'] == row['execution']):
                    candidates.append(row)
            item = {'recommendation': check, 'state': 'unobserved', 'receipt_key': ''}
            if candidates:
                row = max(candidates, key=lambda r: (r['recorded_at'], r['execution'] != 'complete',
                                                      r['result'] != 'pass', r.get('failed', 0)))
                if row['execution'] != 'complete' or row.get('coverage_issues'):
                    state = 'incomplete'
                elif row['result'] != 'pass' or row.get('failed', 0):
                    state = 'failed'
                elif row.get('freshness') != 'fresh':
                    state = 'stale' if row.get('freshness') == 'stale' else 'incomplete'
                elif row.get('counted') and row.get('passed', 0) <= 0:
                    state = 'incomplete'
                else:
                    state = 'current'
                item.update(state=state, receipt_key=row['receipt_key'], result=row['result'],
                            execution=row['execution'], freshness=row['freshness'])
                value['matching_native_receipts'] += 1
            value['checks'].append(item)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
        value.update(state='incomplete', checks=[], matching_native_receipts=0)
        value['issues'].append('Advice observation unavailable: ' + type(error).__name__)
    return value
