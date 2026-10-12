"""Explicit model-free acceptance for standalone OpenAPI contract observations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from core.hosts.provenance import fingerprint
from core.patchproof.openapi import check
from core.patchproof.report import build


def _git(root, *args):
    return subprocess.run(['git', '-c', f'safe.directory={root.as_posix()}', *args],
        cwd=root, capture_output=True, text=True, check=True, timeout=30,
        env={key: value for key, value in os.environ.items() if not key.startswith('GIT_')}).stdout.strip()


def _spec(yaml, removed=False, description=False):
    if yaml:
        return ('openapi: 3.0.3\ninfo:\n  title: Event gateway\n  version: 1.0.0\n' +
                ('  description: More detail\n' if description else '') +
                ('paths: {}\n' if removed else
                 "paths:\n  /events:\n    get:\n      responses:\n        '200':\n          description: ok\n" )).encode()
    return json.dumps({'openapi': '3.0.3', 'info': {'title': 'Stock service', 'version': '1.0.0',
                       **({'description': 'More detail'} if description else {})},
        'paths': {} if removed else {'/stock': {'get': {'responses': {'200': {'description': 'ok'}}}}}}).encode()


def exercise(output, engine):
    output = Path(output).resolve()
    # Each child receives its own fresh Git root; an ancestor repository must
    # neither supply commits nor receive staging/commit operations.
    output.mkdir(parents=True, exist_ok=False)
    projects = []
    for label, yaml in (('stock-python', False), ('gateway-javascript', True)):
        root = output / label
        root.mkdir()
        _git(root, 'init', '-q')
        _git(root, 'config', 'user.name', 'Acceptance')
        _git(root, 'config', 'user.email', 'acceptance@example.invalid')
        _git(root, 'config', 'core.autocrlf', 'false')
        path = 'gateway/openapi.yaml' if yaml else 'schemas/public.json'
        (root / path).parent.mkdir()
        manifest = {'schema': 1, 'contracts': [
            {'id': 'public-api', 'kind': 'openapi', 'path': path},
            {'id': 'secondary-api', 'kind': 'openapi', 'path': 'secondary.json'}]}
        (root / 'elevenpowers.contracts.json').write_bytes(json.dumps(manifest).encode())
        source = root / ('service.js' if yaml else 'service.py')
        source.write_bytes(b'// event service\n' if yaml else b'# stock service\n')
        (root / path).write_bytes(_spec(yaml))
        _git(root, 'add', '.')
        _git(root, 'commit', '-qm', 'Base API')
        (root / path).write_bytes(_spec(yaml, description=True))
        _git(root, 'add', '.')
        _git(root, 'commit', '-qm', 'Compatible documentation')
        started = time.monotonic()
        passing = check(root, 'public-api', engine)
        first = build(root)['contracts']['checks']
        (root / path).write_bytes(_spec(yaml, removed=True))
        _git(root, 'add', '.')
        _git(root, 'commit', '-qm', 'Remove public endpoint')
        failed = check(root, 'public-api', engine)
        second = build(root)['contracts']['checks'][0]
        incomplete = check(root, 'public-api', engine, seconds=0)
        third = build(root)['contracts']['checks'][0]
        check(root, 'public-api', engine)
        (root / path).write_bytes(_spec(yaml))
        stale = build(root)['contracts']['checks'][0]
        projects.append({'project': label, 'format': 'yaml' if yaml else 'json',
            'states': [first[0]['state'], second['state'], third['state'], stale['state'], first[1]['state']],
            'actual_exits': [passing['exit_code'], failed['exit_code'], incomplete['exit_code']],
            'independent_head_matches': failed['head'] == _git(root, 'rev-parse', 'HEAD'),
            'independent_input_matches': failed['inputs']['head']['sha256'] == hashlib.sha256(_spec(yaml, removed=True)).hexdigest(),
            'dirty_association': stale['association'],
            'producer_version': failed['producer']['version'],
            'producer_sha256': failed['producer']['binary_sha256'],
            'configuration_digest': failed['configuration_digest'],
            'seconds': round(time.monotonic() - started, 3)})
    value = {'schema_version': 1, 'model_calls': 0, 'installed_acceptance': False,
             'coding_benefit': 'not_measured', 'runtime_fingerprint': fingerprint(),
             'producer_commit': _git(Path(__file__).resolve().parents[1], 'rev-parse', 'HEAD'),
             'projects': projects}
    (output / 'observations.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--engine', required=True)
    args = parser.parse_args()
    print(json.dumps(exercise(args.output, args.engine), indent=2))


if __name__ == '__main__':
    main()
