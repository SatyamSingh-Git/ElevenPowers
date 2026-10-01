"""Bounded, whitelisted local callback metadata; no raw host payloads."""
import json
import math
from pathlib import Path
import re

PHASES = ('SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'PostToolUseFailure', 'Stop')
MAX_BYTES = 128 * 1024


def read_json(path, maximum=MAX_BYTES):
    path = Path(path)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('linked diagnostic state is unsupported')
    try:
        with path.open('rb') as stream:
            raw = stream.read(maximum + 1)
    except FileNotFoundError:
        return {}
    if len(raw) > maximum:
        raise ValueError('diagnostic state exceeds byte limit')
    return json.loads(raw.decode('utf-8'))


def _hash(value):
    if not isinstance(value, str) or value and not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('invalid diagnostic correlation hash')
    return value


def _count(value):
    if type(value) is not int or not 0 <= value <= 1_000_000_000:
        raise ValueError('invalid diagnostic count')
    return value


def _time(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('invalid diagnostic duration/time')
    return value


def validate(value):
    if not isinstance(value, dict) or any(not isinstance(v, dict) for v in value.values()):
        raise ValueError('invalid integration state')
    clean = {}
    for host, item in value.items():
        data = {}
        for key in ('state', 'generation', 'configuration', 'last_event', 'error', 'last_error'):
            if key in item:
                if not isinstance(item[key], str) or len(item[key]) > 128:
                    raise ValueError('invalid diagnostic text')
                data[key] = item[key]
        for key in ('received', 'processed', 'errors', 'links_evicted'):
            if key in item:
                data[key] = _count(item[key])
        for key in ('configured_at', 'received_at', 'processed_at', 'error_at', 'startup_processed_at'):
            if key in item:
                data[key] = _time(item[key])
        phases = item.get('phases', {})
        if not isinstance(phases, dict) or any(k not in PHASES for k in phases):
            raise ValueError('invalid callback phase set')
        data['phases'] = {}
        for name, phase in phases.items():
            if not isinstance(phase, dict):
                raise ValueError('invalid callback phase')
            part = {k: _count(phase[k]) for k in ('received', 'processed', 'errors') if k in phase}
            part.update({k: _hash(phase[k]) for k in ('task', 'session') if k in phase})
            if 'last_at' in phase:
                part['last_at'] = _time(phase['last_at'])
            if 'last_error' in phase:
                if not isinstance(phase['last_error'], str) or len(phase['last_error']) > 128:
                    raise ValueError('invalid callback error type')
                part['last_error'] = phase['last_error']
            samples = phase.get('samples_ms', [])
            if not isinstance(samples, list) or len(samples) > 32:
                raise ValueError('invalid callback timing sample')
            part['samples_ms'] = [_time(v) for v in samples]
            if 'edit' in phase:
                edit = phase['edit']
                if not isinstance(edit, dict) or type(edit.get('incomplete')) is not bool:
                    raise ValueError('invalid edit diagnostic')
                part['edit'] = {'changed': _count(edit['changed']), 'incomplete': edit['incomplete'],
                                'task': _hash(edit.get('task', '')), 'session': _hash(edit.get('session', ''))}
            data['phases'][name] = part
        links = item.get('receipt_links', [])
        if not isinstance(links, list) or len(links) > 64:
            raise ValueError('invalid native receipt history')
        data['receipt_links'] = []
        for link in links:
            if not isinstance(link, dict) or link.get('result') not in ('pass', 'fail', 'error') or link.get('execution') not in ('complete', 'incomplete'):
                raise ValueError('invalid native receipt link')
            data['receipt_links'].append({k: _hash(link.get(k, '')) for k in ('key', 'task', 'session')} |
                                         {'result': link['result'], 'execution': link['execution'], 'at': _time(link['at'])})
        clean[host] = data
    return clean
