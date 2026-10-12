"""Fresh read-only associations for locally saved contract observations."""
import hashlib
from pathlib import Path
import time

from . import contracts
from .openapi import file_hash

LIMITS = [
    'OpenAPI backward compatibility is scoped to the declared standalone specification and fixed checker policy.',
    'No contract contents, endpoint findings, captured output or executable paths are exported.',
    'Unsigned observations identify producer bytes and configuration; they do not authenticate execution or prove runtime API behavior.',
    'Missing, corrupt, evicted or incomplete history stays explicit; unsupported contracts and external references are not covered.',
]


def _stamp(root):
    values = []
    for path, maximum in ((root / contracts.MANIFEST, 65536), (root / contracts.STATE, 1024 * 1024)):
        try:
            values.append(hashlib.sha256(contracts.bounded(path, maximum)).hexdigest())
        except FileNotFoundError:
            values.append(None)
    return values


def inspect(root, patch, deadline):
    root = Path(root)
    value = {'schema': 1, 'complete': True, 'checks': [], 'issues': [], 'evicted': 0, 'limits': LIMITS}
    declaration = None
    try:
        if time.monotonic() >= deadline:
            raise TimeoutError('contract report deadline reached')
        before = _stamp(root)
        declaration = contracts.declarations(root)
        value['declaration_digest'] = declaration['digest']
        state = contracts.load(root)
        value['evicted'] = state['evicted']
        value['issues'] += declaration['issues']
        value['complete'] = declaration['complete']
        if state['evicted']:
            value['issues'].append('Older contract observations were evicted; retained history is incomplete.')
        for declared in declaration['contracts']:
            matches = [r for r in state['records'] if r['contract_id'] == declared['id']]
            original = max(reversed(matches), key=lambda r: r['checked_at']) if matches else None
            row = {'id': declared['id'], 'property': 'OpenAPI backward compatibility',
                   'path': declared['path'], 'state': 'absent', 'result': 'unknown',
                   'execution': 'unobserved', 'freshness': 'unavailable', 'association': 'unavailable',
                   'issues': [], 'producer': None, 'receipt_id': None}
            if original is not None:
                row.update(result=original['result'], execution=original['execution'],
                           receipt_id=original['id'], recorded_at=original['checked_at'],
                           inputs=original['inputs'], configuration=original['configuration'],
                           manifest_digest=original['manifest_digest'],
                           base=original['base'], head=original['head'], patch_id=original['patch_id'],
                           content_digest=original['content_digest'],
                           configuration_digest=original['configuration_digest'],
                           findings=original['findings'], limits=original['limits'],
                           producer={k: v for k, v in original['producer'].items() if k != 'executable'})
                row['issues'] += original['issues']
                try:
                    path = contracts.safe_path(root, declared['path'])
                    first = file_hash(path, deadline, 2097152)
                    engine = Path(original['producer']['executable'])
                    binary = file_hash(engine, deadline) if original['producer']['executable'] else ''
                    row['freshness'] = ('fresh' if
                        original['manifest_digest'] == declaration['digest'] and
                        original['path'] == declared['path'] and
                        first == original['inputs']['head']['sha256'] and
                        binary == original['producer']['binary_sha256'] and binary and
                        file_hash(path, deadline, 2097152) == first and
                        file_hash(engine, deadline) == binary else 'stale')
                except FileNotFoundError:
                    row['freshness'] = 'gone'
                except (OSError, ValueError, TimeoutError):
                    row['freshness'] = 'unavailable'
                same_patch = all(original[k] == patch[k] and patch[k]
                                 for k in ('base', 'head', 'patch_id', 'content_digest'))
                if same_patch and row['freshness'] == 'fresh' and declaration['complete'] and patch['complete']:
                    row['association'] = 'bound'
                else:
                    row['issues'].append('Recorded contract inputs, declaration, producer or requested patch do not qualify association.')
                row['state'] = ('incomplete' if original['execution'] != 'complete' else
                                'stale' if row['freshness'] != 'fresh' else
                                'current' if original['result'] == 'pass' else 'failed')
            value['checks'].append(row)
        if before != _stamp(root) or declaration != contracts.declarations(root):
            raise ValueError('contract history or declaration changed during inspection')
        if time.monotonic() >= deadline:
            raise TimeoutError('contract report deadline reached')
    except (OSError, ValueError, TypeError, RecursionError, TimeoutError):
        value['complete'] = False
        value['issues'].append('Contract state, declaration or bounded read is unavailable or changed during inspection.')
        if declaration and not value['checks']:
            value['checks'] = [{'id': row['id'], 'path': row['path'],
                'property': 'OpenAPI backward compatibility', 'state': 'unavailable',
                'result': 'unknown', 'execution': 'unobserved', 'freshness': 'unavailable',
                'association': 'unavailable', 'issues': list(value['issues']),
                'producer': None, 'receipt_id': None} for row in declaration['contracts']]
    if not value['complete']:
        for row in value['checks']:
            row['association'] = 'unavailable'
    return value
