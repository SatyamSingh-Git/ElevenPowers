import json
from pathlib import Path

import pytest


def manifest(root, entries=None):
    value = {'schema': 1, 'contracts': entries if entries is not None else [
        {'id': 'api', 'kind': 'openapi', 'path': 'api.json'}]}
    (root / 'elevenpowers.contracts.json').write_text(json.dumps(value), encoding='utf-8')


def record():
    from core.patchproof.contracts import CONFIG, digest
    return {'schema': 1, 'id': 'a' * 32, 'contract_id': 'api', 'kind': 'openapi',
            'path': 'api.json', 'base': 'b' * 40, 'head': 'c' * 40,
            'patch_id': 'd' * 64, 'content_digest': 'e' * 64,
            'manifest_digest': 'f' * 64,
            'inputs': {side: {'sha256': '1' * 64, 'blob': '2' * 40} for side in ('base', 'head')},
            'producer': {'name': 'oasdiff', 'version': '1.33.0', 'binary_sha256': '3' * 64,
                         'executable': str(Path('checker').resolve()), 'platform': 'test'},
            'configuration': CONFIG, 'configuration_digest': digest(CONFIG),
            'limits': {'seconds': 30, 'blob_bytes': 2097152, 'engine_bytes': 134217728},
            'result': 'pass', 'execution': 'complete', 'exit_code': 0,
            'findings': {'info': 0, 'warn': 0, 'error': 0, 'rule_ids': []},
            'issues': [], 'checked_at': 1.0, 'elapsed_seconds': 0.1}


def test_declared_and_absent_contracts(tmp_path):
    from core.patchproof.contracts import declarations
    assert declarations(tmp_path)['contracts'] == []
    manifest(tmp_path)
    value = declarations(tmp_path)
    assert value['complete'] and value['contracts'][0]['path'] == 'api.json'
    assert len(value['digest']) == 64


@pytest.mark.parametrize('entry', [
    {'id': 'api', 'kind': 'openapi', 'path': '../api.json'},
    {'id': 'api', 'kind': 'openapi', 'path': 'C:/api.json'},
    {'id': 'api', 'kind': 'openapi', 'path': '.git/api.json'},
    {'id': 'api', 'kind': 'openapi', 'path': 'api.txt'},
    {'id': 'api', 'kind': 'database', 'path': 'api.json'},
    {'id': 'api space', 'kind': 'openapi', 'path': 'api.json'},
])
def test_bad_declarations_are_visible(tmp_path, entry):
    from core.patchproof.contracts import declarations
    manifest(tmp_path, [entry])
    value = declarations(tmp_path)
    assert not value['complete'] and value['issues']


def test_duplicates_corruption_and_limits(tmp_path):
    from core.patchproof.contracts import declarations
    manifest(tmp_path)
    entry = declarations(tmp_path)['contracts'][0]
    manifest(tmp_path, [entry, entry])
    assert not declarations(tmp_path)['complete']
    (tmp_path / 'elevenpowers.contracts.json').write_text('x' * 65537)
    assert not declarations(tmp_path)['complete']
    (tmp_path / 'elevenpowers.contracts.json').write_text('{broken')
    assert declarations(tmp_path)['issues']


def test_records_retained_bounded_and_corruption_not_reset(tmp_path):
    from core.patchproof.contracts import load, save
    assert load(tmp_path)['records'] == []
    for n in range(65):
        row = record()
        row['id'] = f'{n:032x}'
        save(tmp_path, row)
    value = load(tmp_path)
    assert len(value['records']) == 64 and value['evicted'] == 1
    path = tmp_path / '.elevenpowers/contracts.json'
    path.write_text('{broken')
    before = path.read_bytes()
    with pytest.raises(ValueError):
        save(tmp_path, record())
    assert path.read_bytes() == before


def test_inconsistent_complete_receipt_is_rejected(tmp_path):
    from core.patchproof.contracts import save
    row = record()
    row['result'], row['exit_code'] = 'fail', 0
    with pytest.raises(ValueError):
        save(tmp_path, row)
    row = record()
    row['configuration_digest'] = '4' * 64
    with pytest.raises(ValueError):
        save(tmp_path, row)
