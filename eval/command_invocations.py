"""Model-free process producers and explicit replay qualification, not live hosts."""
import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import time

from core.config import Config, save
from core.ledger import Ledger
from core.milestones import build
from core.process import run


REPO = Path(__file__).resolve().parents[1]
CASES = ('direct', 'wrapped', 'failed', 'wrong_directory', 'interrupted', 'masked_failure')


def shell_command(shell, text):
    if shell == 'system':
        return (text, True)
    if shell != 'bash':
        raise ValueError('unknown producer shell')
    git = shutil.which('git')
    candidates = ([Path(git).resolve().parent.parent / 'bin' / 'bash.exe'] if git and os.name == 'nt' else [])
    if os.name != 'nt' and shutil.which('bash'):
        candidates.append(Path(shutil.which('bash')))
    executable = next((p for p in candidates if p.is_file()), None)
    if executable is None:
        raise FileNotFoundError('Bash producer is unavailable')
    return ([str(executable), '--noprofile', '--norc', '-c', text], False)


def _fixture(root, language, *, faulty=False):
    root.mkdir(parents=True)
    if language == 'python':
        (root / 'app.py').write_text(f'def value():\n    return {4 if faulty else 3}\n')
        (root / 'tests').mkdir()
        (root / 'tests' / 'test_app.py').write_text(
            'import unittest\nfrom app import value\n'
            'class Behavior(unittest.TestCase):\n'
            '    def test_value(self): self.assertEqual(value(), 3)\n')
        return f'"{Path(sys.executable).as_posix()}" -m unittest discover -s tests -v'
    if language == 'javascript':
        if not shutil.which('node') or not shutil.which('npm'):
            raise FileNotFoundError('Node/npm producer is unavailable')
        (root / 'app.mjs').write_text(f'export function value() {{ return {4 if faulty else 3}; }}\n')
        (root / 'check.test.mjs').write_text(
            "import test from 'node:test'; import assert from 'node:assert/strict';\n"
            "import {value} from './app.mjs'; test('behavior', () => assert.equal(value(), 3));\n")
        (root / 'package.json').write_text(json.dumps({'private': True,
            'scripts': {'ci': 'node --test check.test.mjs'}}))
        return 'npm run ci'
    raise ValueError('unknown producer language')


def _observe(root, language, shell, case):
    leaf = _fixture(root, language, faulty=case in {'failed', 'masked_failure'})
    prefix = f'cd "{root.as_posix()}" && '
    command = leaf if case == 'direct' else prefix + leaf
    if case == 'wrong_directory':
        _fixture(root / 'other', language)
        command = 'cd other && ' + leaf
    if case == 'masked_failure':
        command += ' || echo masked'
    save(root, Config(profile='off', commands={'tests': leaf}, strength={'enabled': False}))
    inputs = ['app.py', 'tests/test_app.py'] if language == 'python' else ['app.mjs', 'check.test.mjs', 'package.json']
    (root / 'elevenpowers.milestones.json').write_text(json.dumps({'schema': 1,
        'milestones': [{'id': 'behavior', 'description': 'Behavior remains checked.',
                        'inputs': inputs, 'checks': [{'kind': 'test_suite', 'command': leaf}]}]}))
    Ledger(root=root, task='producer-control').save()
    argv, shell_flag = shell_command(shell, command)
    started = time.monotonic()
    interrupted = False
    try:
        process = run(argv, shell=shell_flag, cwd=root, timeout=0.001 if case == 'interrupted' else 30)
        code = process.returncode
        output = (process.stdout or '') + (process.stderr or '')
    except subprocess.TimeoutExpired:
        code, output, interrupted = None, '', True
    response = {'stdout': output, 'interrupted': True} if interrupted else {'stdout': output, 'exit_code': code}
    # --replay deliberately avoids writing native activation diagnostics.
    callback = subprocess.run([sys.executable, str(REPO / 'plugin/bin/ep_hook.py'), 'PostToolUse', '--replay'],
        shell=False, cwd=root, timeout=30, capture_output=True, text=True, input=json.dumps({'cwd': str(root),
            'tool_name': 'Bash', 'tool_input': {'command': command}, 'tool_response': response}))
    records = [r for r in Ledger.load(root).evidence if r.declaration == 'tests']
    state = build(root)['state']
    expected = ('ABSENT' if case == 'masked_failure' else 'INCOMPLETE' if case in
                {'wrong_directory', 'interrupted'} else 'FAILED' if case == 'failed' else 'CURRENT')
    expected_process = (code is None if case == 'interrupted' else code != 0 if case == 'failed' else code == 0)
    qualified = callback.returncode == 0 and state == expected and expected_process
    if case != 'masked_failure':
        qualified = qualified and len(records) == 1 and records[0].command == command and records[0].declared_command == leaf
    else:
        qualified = qualified and not records
    return {'language': language, 'shell': shell, 'case': case, 'qualified': bool(qualified),
            'process_exit': code, 'callback_exit': callback.returncode, 'interrupted': interrupted,
            'receipt_state': state, 'declared_receipts': len(records),
            'native_activation_written': (root / '.elevenpowers/integrations.json').exists(),
            'seconds': round(time.monotonic() - started, 3),
            'receipts': [{'result': r.result.value, 'execution': r.execution,
                          'provenance_preserved': r.command == command,
                          'declared_identity_preserved': r.declared_command == leaf,
                          'coverage_issues': r.coverage_issues} for r in records]}


def exercise(destination, *, languages=('python', 'javascript'), shells=('system', 'bash')):
    destination = Path(destination).absolute()
    if destination.exists():
        raise ValueError('producer destination must be new')
    if not languages or not shells or set(languages) - {'python', 'javascript'} or set(shells) - {'system', 'bash'}:
        raise ValueError('invalid producer selection')
    destination.mkdir(parents=True)
    from core.hosts.provenance import fingerprint
    value = {'schema': 1, 'runtime': fingerprint(),
             'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'environment': {'python': platform.python_version(), 'platform': platform.platform(),
                             'system_shell': Path(os.environ.get('COMSPEC', '/bin/sh')).name},
             'model_calls': 0,
             'installed_acceptance': False, 'observations': [], 'unavailable': [],
             'limits': ['Actual local commands feed explicit replay callbacks, not installed agent sessions.',
                        'No advice consumption, causal coding improvement or broad shell equivalence is established.']}
    for language in languages:
        for shell in shells:
            for case in CASES:
                try:
                    row = _observe(destination / f'{language}-{shell}-{case}', language, shell, case)
                    value['observations'].append(row)
                except FileNotFoundError as error:
                    value['unavailable'].append({'language': language, 'shell': shell, 'issue': str(error)})
                    break
    value['qualified'] = (not value['unavailable'] and len(value['observations']) == len(languages)*len(shells)*len(CASES)
                          and all(row['qualified'] and not row['native_activation_written'] for row in value['observations']))
    (destination / 'summary.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    value = exercise(args.destination)
    print(json.dumps(value, indent=2))
    return 0 if value['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
