"""Bounded context-emission observations; never evidence of model consumption."""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
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
                _store(path, value)
        except (OSError, ValueError, TypeError, KeyError, RecursionError, Busy):
            # The output has already been flushed. Never alter its decision.
            continue
