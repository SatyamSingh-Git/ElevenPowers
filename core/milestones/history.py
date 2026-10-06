"""Bounded latest observations; storage is part of the ledger's atomic payload."""
from dataclasses import fields
import json
import math

from ..evidence import Evidence
from ..redact import scrub_values
from .definition import KINDS, load

MAX_RECORDS = 256
MAX_BYTES = 4 * 1024 * 1024
FIELDS = {f.name for f in fields(Evidence)}


def _data(item):
    # No deep copy of large inventories or private output just to drop detail.
    value = {name: getattr(item, name) for name in FIELDS}
    value.update(kind=item.kind.value, result=item.result.value, detail='')
    return value


def record(value):
    """Validate metadata before using local unsigned historical observations."""
    if not isinstance(value, dict) or set(value) - FIELDS:
        raise ValueError('invalid milestone receipt fields')
    if not {'kind', 'identity', 'result', 'observed', 'tree', 'command', 'at'} <= set(value):
        raise ValueError('missing milestone receipt fields')
    item = Evidence.from_dict({**value, 'detail': ''})
    if (item.kind.value not in KINDS or not isinstance(item.command, str) or not item.command
            or len(item.command) > 4096 or not isinstance(item.identity, str) or not item.identity
            or len(item.identity) > 4096 or not isinstance(item.tree, str) or not item.tree
            or len(item.tree) > 256 or type(item.at) not in (int, float)
            or not math.isfinite(item.at) or item.at <= 0
            or item.execution not in {'complete', 'incomplete'} or item.scope not in {'', 'source'}
            or type(item.counted) is not bool
            or any(type(n) is not int or n < 0 for n in (item.passed, item.failed))):
        raise ValueError('invalid milestone receipt metadata')
    if (not isinstance(item.observed, list) or len(item.observed) > 20000
            or any(not isinstance(p, str) or not p or len(p) > 2048 for p in item.observed)
            or len(set(item.observed)) != len(item.observed)
            or not isinstance(item.coverage_issues, list)
            or any(not isinstance(p, str) or len(p) > 4096 for p in item.coverage_issues)
            or any(not isinstance(v, str) or len(v) > 4096
                   for v in (item.declaration, item.declared_command, item.run, item.vcs))):
        raise ValueError('invalid milestone receipt scope')
    item.detail = ''
    return item


def read(value):
    if value == {}:
        return [], []
    if (not isinstance(value, dict) or set(value) != {'schema', 'receipts', 'issues'}
            or type(value.get('schema')) is not int or value['schema'] != 1
            or not isinstance(value.get('receipts'), list)
            or not isinstance(value.get('issues'), list)
            or any(not isinstance(i, str) or len(i) > 1024 for i in value['issues'])):
        return [], ['milestone history metadata is invalid']
    issues = value['issues'][:32]
    if len(value['issues']) > 32 or len(value['receipts']) > MAX_RECORDS:
        issues.append('milestone history exceeds its record or diagnostic budget')
    records = []
    for raw in value['receipts'][-MAX_RECORDS:]:
        try:
            records.append(record(raw))
        except (ValueError, TypeError, KeyError, AttributeError):
            issues.append('milestone history contains invalid receipt metadata')
    return records, list(dict.fromkeys(issues))[:32]


def retain(root, prior, records):
    definition = load(root)
    existing, issues = read(prior)
    issues += definition['issues']
    wanted = {(c['kind'], c['command']) for m in definition['milestones'] for c in m['checks']}
    latest = {}
    for item in existing:
        key = item.kind.value, item.command
        if key not in latest or item.at >= latest[key].at:
            latest[key] = item
    for item in records:
        try:
            key = item.kind.value, item.command
            if key not in wanted:
                continue
            item = record(_data(item))
            if key not in latest or item.at >= latest[key].at:
                latest[key] = item
        except (ValueError, TypeError, KeyError, AttributeError):
            issues.append('milestone history could not retain invalid receipt metadata')
    kept = sorted(latest.values(), key=lambda e: e.at)[-MAX_RECORDS:]
    if len(latest) > MAX_RECORDS:
        issues.append('milestone history command identity limit reached; older observations omitted')
    value = {'schema': 1, 'receipts': [], 'issues': list(dict.fromkeys(issues))[:32]}
    # Account for row indentation once rather than repeatedly serializing an
    # oversized whole history while removing one item at a time under the lock.
    size = len(json.dumps(value, indent=2).encode('utf-8')) + 256
    for item in reversed(kept):
        data = _data(item)
        encoded = json.dumps(data, indent=2).encode('utf-8')
        cost = len(encoded) + 4 * (encoded.count(b'\n') + 1) + 2
        if size + cost > MAX_BYTES:
            notice = 'milestone history byte limit reached; older observations omitted'
            if notice not in value['issues']:
                value['issues'].append(notice)
            continue
        size += cost
        value['receipts'].insert(0, data)
    return scrub_values(value)
