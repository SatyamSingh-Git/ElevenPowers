"""Explicit disposable Python/JavaScript PatchProof controls; no model calls."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

from core.evidence import Kind, source_snapshot
from core.ledger import Ledger
from core.parsers import parse
from core.patchproof.report import build
from core.process import run


def _command(args):
    return subprocess.list2cmdline(args) if os.name == 'nt' else shlex.join(args)


def _git(root, *args):
    return subprocess.check_output(['git', '-c', f'safe.directory={root.as_posix()}', *args],
                                   cwd=root).strip().decode()


def _commit(root):
    _git(root, 'add', '--all')
    _git(root, '-c', 'user.name=PatchProof control', '-c', 'user.email=control@example.invalid',
         'commit', '-qm', 'exercise stage')
    return _git(root, 'rev-parse', 'HEAD')


def _execute(root, command, *, seconds=10):
    before = source_snapshot(root, fresh=True)
    env = {**os.environ, 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PYTHONDONTWRITEBYTECODE': '1',
           'PYTEST_ADDOPTS': '', 'PYTEST_PLUGINS': '', 'PYTHONNOUSERSITE': '1'}
    started = time.monotonic()
    try:
        done = run(command, cwd=root, timeout=seconds, env=env)
        code, output = done.returncode, done.stdout + done.stderr
    except subprocess.TimeoutExpired as exc:
        code, output = None, (exc.stdout or '') + (exc.stderr or '')
    records = parse(command, output, code, root, snapshot=before)
    if code is None:
        for record in records:
            record.execution = 'incomplete'
    ledger = Ledger.load(root)
    ledger.add(records)
    ledger.save()
    return {'exit_code': code, 'seconds': round(time.monotonic() - started, 3),
            'records': len(records), 'suite_counts': [{'passed': r.passed, 'failed': r.failed}
                                                      for r in records if r.kind is Kind.SUITE]}


def exercise(destination):
    destination = Path(destination).absolute()
    if destination.exists():
        raise ValueError('exercise destination must be a new disposable directory')
    if not shutil.which('node'):
        raise ValueError('Node is required for both project controls')
    destination.mkdir(parents=True)
    projects = []
    for language in ('python', 'javascript'):
        root = destination / language
        root.mkdir()
        _git(root, 'init', '-q')
        _git(root, 'config', 'core.autocrlf', 'false')
        if language == 'python':
            path, base_source, good, bad = 'service.py', 'value=0\n', 'value=2\n', 'value=3\n'
            (root / 'test_service.py').write_text('from service import value\ndef test_value():\n    assert value == 2\n', newline='\n')
            command = _command([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'])
        else:
            path, base_source, good, bad = 'service.cjs', 'exports.value=0;\n', 'exports.value=2;\n', 'exports.value=3;\n'
            (root / 'service.test.cjs').write_text("const test=require('node:test'); const assert=require('node:assert/strict');\ntest('value',()=>assert.equal(require('./service.cjs').value,2));\n", newline='\n')
            command = _command([shutil.which('node'), '--test', 'service.test.cjs'])
        source = root / path
        source.write_text(base_source, newline='\n')
        base = _commit(root)
        source.write_text(good, newline='\n')
        head = _commit(root)
        state = root / '.elevenpowers'
        state.mkdir()
        interrupted = _command([sys.executable, '-c', 'import time; time.sleep(10)'])
        (state / 'config.json').write_text(json.dumps({'auto_detect': False, 'commands': {
            'tests': command, 'build': interrupted, 'typecheck': 'unrun-control'}}), newline='\n')
        runs = [_execute(root, command)]
        passing = build(root, base, head)
        assert passing['binding']['state'] == 'bound'
        source.write_text(bad, newline='\n')
        faulty_head = _commit(root)
        runs.append(_execute(root, command))
        failed = build(root, head, faulty_head)
        assert failed['binding']['state'] == 'bound'
        runs.append(_execute(root, interrupted, seconds=.1))
        incomplete = build(root, head, faulty_head)
        (root / 'extra.json').write_text('{}', newline='\n')
        dirty = build(root, head, faulty_head)
        states = [next(c['state'] for c in passing['checks'] if c['property'] == 'tests'),
                  next(c['state'] for c in failed['checks'] if c['property'] == 'tests'),
                  next(c['state'] for c in incomplete['checks'] if c['property'] == 'build'),
                  next(c['state'] for c in incomplete['checks'] if c['property'] == 'typecheck')]
        projects.append({'language': language, 'states': states, 'runs': runs,
                         'exit_codes': [r['exit_code'] for r in runs],
                         'dirty_binding': dirty['binding']['state'],
                         'independent_head_matches': incomplete['patch']['head'] == _git(root, 'rev-parse', 'HEAD'),
                         'base': base, 'head': faulty_head,
                         'patch_id': incomplete['patch']['patch_id']})
    return {'schema_version': 1, 'model_calls': 0, 'installed_acceptance': False,
            'coding_benefit': 'not measured', 'projects': projects}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = exercise(args.output)
    (args.output / 'observations.json').write_text(json.dumps(value, indent=2) + '\n', newline='\n')
    print(json.dumps(value, indent=2))


if __name__ == '__main__':
    main()
