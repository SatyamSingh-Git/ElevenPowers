"""Project-owned applicability and bounded unsigned contract observations."""
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from ..hosts.setup import _write
from ..jobs import ledger_write
from ..ledger import _keep_out_of_git
MANIFEST = 'elevenpowers.contracts.json'
STATE = '.elevenpowers/contracts.json'
CONFIG = {'schema': 1, 'adapter': 'openapi-v1', 'version': '1.33.0', 'validate_fail_on': 'WARN', 'breaking_fail_on': 'ERR', 'external_refs': False, 'checker_config': {}}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def bounded(path, limit):
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('linked contract state/input is unsupported')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('contract read budget exceeded')
    return raw

def _path(value):
    if not isinstance(value, str) or not value or len(value) > 1024 or any((c in value for c in ('\\', ':', '\x00', '\n', '\r'))):
        raise ValueError('invalid contract path')
    path = PurePosixPath(value)
    if path.is_absolute() or any((p in ('..', '.git', '.elevenpowers') for p in path.parts)) or path.as_posix() != value or (path.suffix.lower() not in ('.json', '.yaml', '.yml')):
        raise ValueError('unsupported contract path')
    return path

def safe_path(root, value):
    _path(value)
    target = root / value
    if target.resolve() != target.absolute() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('linked or escaped contract input')
    return target

def declarations(root):
    root = Path(root)
    value = {'contracts': [], 'digest': '', 'complete': True, 'issues': []}
    try:
        raw = bounded(root / MANIFEST, 65536)
        data = json.loads(raw)
        if not isinstance(data, dict) or set(data) != {'schema', 'contracts'} or type(data['schema']) is not int or (data['schema'] != 1) or (not isinstance(data['contracts'], list)) or (len(data['contracts']) > 16):
            raise ValueError('invalid contract manifest')
        seen = set()
        for row in data['contracts']:
            if not isinstance(row, dict) or set(row) != {'id', 'kind', 'path'} or (not isinstance(row['id'], str)) or (not re.fullmatch('[A-Za-z0-9_-]{1,64}', row['id'])) or (row['id'] in seen) or (row['kind'] != 'openapi'):
                raise ValueError('duplicate, invalid or unsupported contract declaration')
            safe_path(root, row['path'])
            seen.add(row['id'])
            value['contracts'].append(row)
        value['digest'] = hashlib.sha256(raw).hexdigest()
    except FileNotFoundError:
        pass
    except (OSError, ValueError, TypeError, RecursionError):
        value['complete'] = False
        value['issues'].append('Contract manifest is malformed, linked, unsupported or exceeds limits.')
    return value

def _hex(value, lengths=(64,), empty=False):
    return isinstance(value, str) and (empty and value == '' or (len(value) in lengths and re.fullmatch('[0-9a-f]+', value) is not None))

def _require(condition):
    if not condition:
        raise ValueError('invalid contract observation')

def validate(row):
    required = {'schema', 'id', 'contract_id', 'kind', 'path', 'base', 'head', 'patch_id', 'content_digest', 'manifest_digest', 'inputs', 'producer', 'configuration', 'configuration_digest', 'limits', 'result', 'execution', 'exit_code', 'findings', 'issues', 'checked_at', 'elapsed_seconds'}
    try:
        _require(isinstance(row, dict) and set(row) == required and (type(row['schema']) is int) and (row['schema'] == 1))
        _require(_hex(row['id'], (32,)) and re.fullmatch('[A-Za-z0-9_-]{1,64}', row['contract_id']))
        _require(row['kind'] == 'openapi')
        _path(row['path'])
        for key in ('base', 'head'):
            _require(_hex(row[key], (40, 64), empty=True))
        for key in ('patch_id', 'content_digest', 'manifest_digest'):
            _require(_hex(row[key], empty=True))
        _require(set(row['inputs']) == {'base', 'head'})
        for entry in row['inputs'].values():
            _require(set(entry) == {'sha256', 'blob'} and _hex(entry['sha256'], empty=True) and _hex(entry['blob'], (40, 64), empty=True))
        producer = row['producer']
        _require(set(producer) == {'name', 'version', 'binary_sha256', 'executable', 'platform'})
        _require(producer['name'] == 'oasdiff' and producer['version'] in ('', '1.33.0'))
        _require(_hex(producer['binary_sha256'], empty=True))
        _require(all((isinstance(producer[key], str) and len(producer[key]) <= 4096 and ('\x00' not in producer[key]) for key in ('executable', 'platform'))))
        _require(row['configuration'] == CONFIG and row['configuration_digest'] == digest(CONFIG))
        _require(set(row['limits']) == {'seconds', 'blob_bytes', 'engine_bytes'})
        _require(row['limits']['blob_bytes'] == 2097152 and row['limits']['engine_bytes'] == 134217728)
        _require(type(row['limits']['seconds']) in (int, float) and math.isfinite(row['limits']['seconds']) and (0 <= row['limits']['seconds'] <= 600))
        _require(row['result'] in ('pass', 'fail', 'unknown') and row['execution'] in ('complete', 'incomplete'))
        _require(row['exit_code'] is None or type(row['exit_code']) is int)
        findings = row['findings']
        _require(set(findings) == {'info', 'warn', 'error', 'rule_ids'})
        _require(all((type(findings[k]) is int and 0 <= findings[k] <= 100000 for k in ('info', 'warn', 'error'))))
        _require(isinstance(findings['rule_ids'], list) and len(findings['rule_ids']) <= 256)
        _require(all((isinstance(rule, str) and re.fullmatch('[a-z0-9_-]{1,128}', rule) for rule in findings['rule_ids'])))
        _require(isinstance(row['issues'], list) and len(row['issues']) <= 16)
        _require(all((isinstance(issue, str) and len(issue) <= 256 for issue in row['issues'])))
        for key in ('checked_at', 'elapsed_seconds'):
            _require(type(row[key]) in (int, float) and math.isfinite(row[key]) and (0 <= row[key] <= 10 ** 12))
        if row['execution'] == 'complete':
            _require(row['result'] in ('pass', 'fail') and (not row['issues']))
            _require(row['exit_code'] == (0 if row['result'] == 'pass' else 1))
            _require((findings['error'] == 0) == (row['result'] == 'pass'))
            _require(all((row[k] for k in ('base', 'head', 'patch_id', 'content_digest', 'manifest_digest'))))
            _require(all((entry['sha256'] and entry['blob'] for entry in row['inputs'].values())))
            _require(producer['binary_sha256'] and producer['version'] == '1.33.0' and producer['executable'])
        else:
            _require(row['result'] == 'unknown')
    except (AssertionError, KeyError, TypeError, ValueError):
        raise ValueError('invalid contract observation') from None

def load(root):
    try:
        value = json.loads(bounded(Path(root) / STATE, 1024 * 1024))
    except FileNotFoundError:
        return {'schema': 1, 'records': [], 'evicted': 0}
    if not isinstance(value, dict) or set(value) != {'schema', 'records', 'evicted'} or type(value['schema']) is not int or (value['schema'] != 1) or (not isinstance(value['records'], list)) or (len(value['records']) > 64) or (type(value['evicted']) is not int) or (not 0 <= value['evicted'] <= 10 ** 9):
        raise ValueError('invalid contract history')
    for row in value['records']:
        validate(row)
    return value

def save(root, row):
    root = Path(root)
    validate(row)
    state = root / '.elevenpowers'
    if state.is_symlink() or state.resolve() != state.absolute():
        raise ValueError('linked contract history')
    state.mkdir(exist_ok=True)
    _keep_out_of_git(state)
    if (state / 'ledger.lock').is_symlink():
        raise ValueError('linked contract ownership')
    with ledger_write(root):
        value = load(root)
        value['records'].append(row)
        while len(value['records']) > 64 or len((json.dumps(value, indent=2) + '\n').encode()) > 1024 * 1024:
            value['records'].pop(0)
            value['evicted'] = min(10 ** 9, value['evicted'] + 1)
        _write(root / STATE, value)
