"""Reuse completed samples only for exact project and execution inputs."""
import hashlib
import json
import os
import platform
import sys


def execution_stamp(files):
    # Environment values affect tests, but only a one-way fingerprint is saved.
    context = json.dumps({'environment': sorted(os.environ.items()),
                          'python': sys.version, 'executable': sys.executable,
                          'platform': platform.platform()}, ensure_ascii=True)
    return hashlib.sha256((files + context).encode('utf-8')).hexdigest()


def reusable(value, *, task, base, command, settings, fingerprint, paths, versions):
    if not value or value.get('state') not in ('complete', 'incomplete') or value.get('baseline') != 'passed':
        return False
    if value.get('summary', {}).get('incomplete'):
        return False
    if any(not issue.startswith('mutation attempt limit') for issue in value.get('issues', [])):
        return False
    expected = dict(task=task, base=base, command=command, settings=settings,
                    fingerprint=fingerprint, paths=paths, engine_versions=versions)
    # JSON normalizes tuple/list settings in the persisted contract.
    return all(value.get(key) == json.loads(json.dumps(item)) for key, item in expected.items())
