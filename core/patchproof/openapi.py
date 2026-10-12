"""Explicit, bounded oasdiff observations over two committed specification blobs."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid

from ..process import run
from . import contracts
from .identity import collect, GitRead


def file_hash(path, deadline, maximum=134217728):
    digest, count = hashlib.sha256(), 0
    with Path(path).open('rb') as stream:
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError('contract deadline reached')
            part = stream.read(min(65536, maximum - count + 1))
            if not part:
                return digest.hexdigest()
            count += len(part)
            if count > maximum:
                raise ValueError('contract input exceeds read limit')
            digest.update(part)


def findings(output, code, *, validating=False):
    value = contracts.json_read(output)
    if not isinstance(value, list) or len(value) > 100000:
        raise ValueError('unsupported checker output')
    counts = {'info': 0, 'warn': 0, 'error': 0, 'rule_ids': []}
    rules = set()
    for row in value:
        if (not isinstance(row, dict) or type(row.get('level')) is not int
                or row['level'] not in (1, 2, 3) or not isinstance(row.get('id'), str)
                or not re.fullmatch('[a-z0-9_-]{1,128}', row['id'])):
            raise ValueError('unsupported checker finding')
        counts[{1: 'info', 2: 'warn', 3: 'error'}[row['level']]] += 1
        rules.add(row['id'])
    if len(rules) > 256:
        raise ValueError('checker rule summary exceeds limit')
    counts['rule_ids'] = sorted(rules)
    rejected = counts['error'] + (counts['warn'] if validating else 0) > 0
    if code != (1 if rejected else 0):
        raise ValueError('checker exit code and findings disagree')
    return counts


def _json_input(raw, suffix):
    # The real YAML loader rejects duplicate mappings. JSON-form YAML still
    # needs the strict JSON path because the producer accepts duplicate names.
    if suffix == '.json':
        contracts.json_read(raw)
    else:
        try:
            contracts.json_read(raw)
        except json.JSONDecodeError:
            pass  # Actual YAML is validated/parsed by the pinned producer.


def _standalone(output):
    value = contracts.json_read(output)
    if not isinstance(value, dict) or not isinstance(value.get('openapi'), str):
        raise ValueError('unsupported canonical contract')
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > 128:
            raise ValueError('contract structure exceeds supported depth')
        if isinstance(item, dict):
            if any(key in item for key in contracts.UNSUPPORTED_SCHEMA_KEYS):
                raise ValueError('dynamic, recursive or custom schema dialect semantics are unsupported')
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)


def _blob(git, commit, path):
    entry = git.read('ls-tree', '-z', commit, '--', path)
    pieces = entry.rstrip(b'\0').split(b'\t')
    if len(pieces) != 2 or pieces[1].decode('utf-8') != path:
        raise ValueError('declared contract blob is absent')
    mode, kind, identity = pieces[0].split(b' ')
    if mode not in (b'100644', b'100755') or kind != b'blob':
        raise ValueError('declared contract is not a regular committed file')
    size = int(git.read('cat-file', '-s', identity.decode('ascii')))
    if not 0 <= size <= 2097152:
        raise ValueError('committed contract exceeds blob budget')
    raw = git.read('cat-file', 'blob', identity.decode('ascii'))
    if len(raw) != size:
        raise ValueError('committed contract size changed')
    return raw, {'sha256': hashlib.sha256(raw).hexdigest(), 'blob': identity.decode('ascii')}


def check(root, contract_id, engine, base='HEAD~1', head='HEAD', *, seconds=30):
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 <= seconds <= 600:
        raise ValueError('contract seconds must be between 0 and 600')
    root = Path(root).resolve(strict=True)
    declaration = contracts.declarations(root)
    selected = next((row for row in declaration['contracts'] if row['id'] == contract_id), None)
    if not declaration['complete'] or selected is None:
        raise ValueError('a valid supported declared contract is required')
    contracts.load(root)  # Never run a checker then silently replace damaged history.
    started = time.monotonic()
    deadline = started + seconds
    row = {'schema': 1, 'id': uuid.uuid4().hex, 'contract_id': contract_id,
           'kind': 'openapi', 'path': selected['path'], 'base': '', 'head': '',
           'patch_id': '', 'content_digest': '', 'manifest_digest': declaration['digest'],
           'inputs': {side: {'sha256': '', 'blob': ''} for side in ('base', 'head')},
           'producer': {'name': 'oasdiff', 'version': '', 'binary_sha256': '',
                        'executable': '', 'platform': sys.platform},
           'configuration': contracts.CONFIG, 'configuration_digest': contracts.digest(contracts.CONFIG),
           'limits': {'seconds': seconds, 'blob_bytes': 2097152, 'engine_bytes': 134217728},
           'result': 'unknown', 'execution': 'incomplete', 'exit_code': None,
           'findings': {'info': 0, 'warn': 0, 'error': 0, 'rule_ids': []},
           'issues': [], 'checked_at': time.time(), 'elapsed_seconds': 0.0}
    phase = 'resolve committed inputs'
    try:
        patch = collect(root, base, head, seconds=max(0, deadline - time.monotonic()))
        if not patch['complete']:
            raise ValueError('committed patch unavailable')
        for key in ('base', 'head', 'patch_id', 'content_digest'):
            row[key] = patch[key]
        git = GitRead(root, deadline)
        data = {}
        for side in ('base', 'head'):
            data[side], row['inputs'][side] = _blob(git, patch[side], selected['path'])
            _json_input(data[side], Path(selected['path']).suffix.lower())
        executable = Path(engine).resolve(strict=True)
        if not executable.is_file():
            raise ValueError('checker executable unavailable')
        producer = row['producer']
        producer['executable'] = str(executable)
        producer['binary_sha256'] = file_hash(executable, deadline)
        env = {key: value for key, value in os.environ.items() if not key.startswith('OASDIFF_')}
        with tempfile.TemporaryDirectory(prefix='ep-openapi-') as directory:
            private = Path(directory)
            config = private / 'config.yaml'
            config.write_bytes(b'{}\n')

            def execute(*args):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('contract deadline reached')
                done = run([str(executable), '--config', str(config), *args],
                           cwd=private, env=env, shell=False, timeout=remaining)
                row['exit_code'] = done.returncode
                if done.stderr:
                    raise ValueError('checker emitted diagnostics')
                return done

            phase = 'identify checker'
            version = execute('--version')
            if version.returncode or version.stdout.strip() != 'oasdiff version 1.33.0':
                raise ValueError('unsupported oasdiff version; require 1.33.0')
            producer['version'] = '1.33.0'
            paths = {}
            for side in ('base', 'head'):
                path = private / (side + Path(selected['path']).suffix.lower())
                path.write_bytes(data[side])
                paths[side] = str(path)
                phase = 'validate ' + side
                done = execute('validate', '--format', 'json', '--fail-on', 'WARN',
                               '--allow-external-refs=false', '--', str(path))
                validated = findings(done.stdout, done.returncode, validating=True)
                if validated['error'] or validated['warn']:
                    raise ValueError('contract validation reported WARN or ERR findings')
                phase = 'qualify standalone ' + side
                canonical = execute('upgrade', '--format', 'json', '--allow-external-refs=false', '--', str(path))
                if canonical.returncode:
                    raise ValueError('canonical contract unavailable')
                _standalone(canonical.stdout)
            phase = 'compare contracts'
            done = execute('breaking', '--format', 'json', '--fail-on', 'ERR',
                           '--allow-external-refs=false', '--', paths['base'], paths['head'])
            row['findings'] = findings(done.stdout, done.returncode)
        phase = 'recheck provenance'
        if file_hash(executable, deadline) != producer['binary_sha256']:
            raise ValueError('checker executable changed during inspection')
        if contracts.declarations(root) != declaration:
            raise ValueError('contract declaration changed during inspection')
        final = collect(root, base, head, seconds=max(0, deadline - time.monotonic()))
        if final != patch:
            raise ValueError('patch or checkout changed during inspection')
        row['result'] = 'fail' if row['findings']['error'] else 'pass'
        row['execution'] = 'complete'
    except (OSError, ValueError, UnicodeError, TypeError, RecursionError, TimeoutError, subprocess.SubprocessError):
        # Raw producer diagnostics can contain contract contents, paths or credentials.
        row['issues'].append('OpenAPI compatibility incomplete during ' + phase + '; inspect format, checker, policy and recorded limits.')
    row['elapsed_seconds'] = round(time.monotonic() - started, 6)
    contracts.save(root, row)
    return row
