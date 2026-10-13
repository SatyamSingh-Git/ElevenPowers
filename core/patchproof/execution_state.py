"""Bounded unsigned command associations and freshly read execution witnesses."""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
import time
import uuid

from ..config import load
from ..evidence import source_snapshot
from ..hosts.provenance import fingerprint
from ..jobs import replace
from .identity import collect
from .policy import fingerprint as policy_fingerprint
from ..inputs.collection import capture as input_capture

FILE = 'patch-verification.json'
MAX_BYTES = 1024 * 1024
MAX_ATTEMPTS = 128


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                    separators=(',', ':')).encode()).hexdigest()


def path(root):
    target = Path(root) / '.elevenpowers' / FILE
    if (target.is_symlink() or target.parent.is_symlink()
            or target.parent.resolve() != target.parent.absolute()):
        raise ValueError('linked patch verification state is unsupported')
    return target


def read(root):
    target = path(root)
    if not target.exists():
        return {'schema': 1, 'attempts': [], 'evicted': 0}
    with target.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('patch verification state exceeds read budget')
    def unique(pairs):
        result = {}
        for name, value in pairs:
            if name in result:
                raise ValueError('duplicate patch verification state key')
            result[name] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=unique)
    except RecursionError as error:
        raise ValueError('patch verification state nesting is unsupported') from error
    if (not isinstance(value, dict) or type(value.get('schema')) is not int or value.get('schema') != 1
            or not isinstance(value.get('attempts'), list)
            or len(value['attempts']) > MAX_ATTEMPTS
            or type(value.get('evicted')) is not int or value['evicted'] < 0):
        raise ValueError('invalid patch verification state')
    for item in value['attempts']:
        if (not isinstance(item, dict) or item.get('status') not in
                {'incomplete', 'passed', 'failed', 'stale'}
                or not isinstance(item.get('witness'), dict)
                or not isinstance(item.get('receipt_keys'), list)
                # Older schema-1 writers retained individual pytest keys. Keep
                # their bounded history readable; new writers use aggregates.
                or len(item['receipt_keys']) > MAX_BYTES // 64
                or not all(isinstance(k, str) and len(k) == 64 for k in item['receipt_keys'])
                or not isinstance(item.get('command_digest'), str)
                or len(item['command_digest']) != 64
                or not isinstance(item.get('properties'), list)
                or len(item['properties']) > 64
                or not all(isinstance(p, str) and len(p) <= 128 for p in item['properties'])):
            raise ValueError('invalid patch verification attempt')
        _witness_shape(item['witness'])
        if item.get('after') is not None:
            _witness_shape(item['after'])
        from ..parsers import DECLARED_KINDS
        if not item['properties'] or any(p not in DECLARED_KINDS for p in item['properties']):
            raise ValueError('unsupported saved verification property')
        bounds = item.get('budgets')
        if (not isinstance(bounds, dict) or set(bounds) != {'seconds', 'command_seconds',
                'output_bytes_per_command', 'cleanup_seconds_per_command', 'max_declarations'}
                or type(bounds['seconds']) not in (int, float) or not 0 < bounds['seconds'] <= 600
                or type(bounds['command_seconds']) not in (int, float) or not 0 < bounds['command_seconds'] <= 300
                or bounds['output_bytes_per_command'] != 8 * 1024 * 1024
                or bounds['cleanup_seconds_per_command'] != 5 or bounds['max_declarations'] != 64):
            raise ValueError('unsupported saved verification bounds')
    return value


def _witness_shape(value):
    sizes = {'patch_id': (64,), 'head': (40, 64), 'content_digest': (64,),
             'source_fingerprint': (16,), 'configuration_fingerprint': (64,),
             'policy_fingerprint': (64,), 'producer_fingerprint': (64,),
             'environment_fingerprint': (64,)}
    if isinstance(value,dict) and 'external_inputs_fingerprint' in value:
        sizes['external_inputs_fingerprint'] = (64,)
    if (not isinstance(value, dict) or set(value) != set(sizes)
            or any(not isinstance(v, str) or len(v) not in sizes[k]
                   or re.fullmatch('[0-9a-f]+', v) is None for k, v in value.items())):
        raise ValueError('unsupported saved verification witness')


def save(root, value):
    target = path(root)
    data = json.dumps(value, ensure_ascii=True, indent=2).encode()
    while len(data) > MAX_BYTES and len(value['attempts']) > 1:
        value['attempts'].pop(0)
        value['evicted'] += 1
        data = json.dumps(value, ensure_ascii=True, indent=2).encode()
    if len(data) > MAX_BYTES:
        raise ValueError('patch verification state exceeds write budget')
    temporary = target.with_suffix('.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def retain(value, item):
    value['attempts'].append(item)
    excess = max(0, len(value['attempts']) - MAX_ATTEMPTS)
    if excess:
        value['attempts'] = value['attempts'][excess:]
        value['evicted'] += excess


def _source_witness(root, patch, deadline, *, base=None, head=None):
    """Return a qualification plus actual parser snapshot; never export env values."""
    if time.monotonic() >= deadline:
        raise TimeoutError('verification deadline reached before input inspection')
    actual = collect(root, base if base is not None else patch['base'],
                     head if head is not None else patch['head'],
                     seconds=max(0, deadline - time.monotonic()))
    if (not actual['complete'] or not actual['checkout']['eligible']
            or actual['patch_id'] != patch['patch_id']
            or actual['content_digest'] != patch['content_digest']):
        raise ValueError('patch or checkout is no longer eligible for execution')
    snapshot = source_snapshot(root, fresh=True, deadline=deadline)
    if not snapshot[0].complete:
        raise ValueError('source coverage is incomplete for execution')
    configuration = root / '.elevenpowers/config.json'
    if configuration.is_symlink() or configuration.parent.is_symlink():
        raise ValueError('linked command configuration is unsupported')
    raw = b''
    if configuration.exists():
        with configuration.open('rb') as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('command configuration exceeds read budget')
        decoded = json.loads(raw)
        if not isinstance(decoded, dict):
            raise ValueError('command configuration must be an object')
    config = load(root)
    if not config.verifies:
        raise ValueError('off profile refuses command execution')
    value = {'patch_id': actual['patch_id'], 'head': actual['head'],
             'content_digest': actual['content_digest'], 'source_fingerprint': snapshot[1],
             'configuration_fingerprint': digest([hashlib.sha256(raw).hexdigest(), config.__dict__]),
             'policy_fingerprint': policy_fingerprint(root, deadline),
             'producer_fingerprint': fingerprint(),
             'environment_fingerprint': digest([sys.version, sys.executable, platform.platform(),
                                                str(root), dict(os.environ)])}
    return value, snapshot


def witness(root, patch, deadline, *, base=None, head=None):
    """External collection cannot preserve an earlier source qualification."""
    value, snapshot = _source_witness(root,patch,deadline,base=base,head=head)
    external = input_capture(root,deadline)
    if external['state'] != 'not_configured':
        final, _ = _source_witness(root,patch,deadline,base=base,head=head)
        if final != value:
            raise ValueError('source or execution inputs changed during external inspection')
    if external['state'] == 'incomplete':
        raise ValueError('required external input observation is incomplete')
    if external['state'] == 'available':
        value['external_inputs_fingerprint'] = external['fingerprint']
    if time.monotonic() >= deadline:
        raise TimeoutError('verification deadline reached during input inspection')
    return value, snapshot
