"""Explicit disposable milestone controls; no agent or model is launched."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from core.evidence import Kind, Result, source_snapshot, tree_hash
from core.export import write
from core.ledger import Ledger
from core.milestones import build
from core.parsers import parse
from core.process import run

# Controller-owned expectations are fixed before any faulty source is applied.
PROVIDER = 'def expired(tick, expiry):\n    return tick >= expiry\n'
FAULT = 'def expired(tick, expiry):\n    return tick > expiry\n'
EQUIVALENT = 'def expired(tick, expiry):\n    return tick > expiry or tick == expiry\n'
CONSUMER = 'from provider import expired\n\ndef checkout(tick, expiry):\n    return 403 if expired(tick, expiry) else 200\n'
WORKER = 'from consumer import checkout\n\ndef process(tick, expiry):\n    return "processed" if checkout(tick, expiry) == 200 else "denied"\n'
CHECKS = {
    'provider': 'from provider import expired\n\ndef test_before_expiry():\n    assert expired(9, 10) is False\n\ndef test_expiry_boundary():\n    assert expired(10, 10) is True\n    assert expired(11, 10) is True\n',
    'checkout': 'from consumer import checkout\n\ndef test_valid_checkout():\n    assert checkout(9, 10) == 200\n\ndef test_expired_checkout():\n    assert checkout(10, 10) == 403\n    assert checkout(11, 10) == 403\n',
    'worker': 'from worker import process\n\ndef test_valid_work():\n    assert process(9, 10) == "processed"\n\ndef test_expired_work():\n    assert process(10, 10) == "denied"\n    assert process(11, 10) == "denied"\n',
}


def _put(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def _command(args):
    return subprocess.list2cmdline(args) if os.name == 'nt' else shlex.join(args)


class Producer:
    def __init__(self, destination):
        self.directory = destination
        self.logs = destination / 'logs'
        self.logs.mkdir()
        self.deadline = time.monotonic() + 120
        self.runs = []

    def python(self, name):
        return _command([sys.executable, '-m', 'pytest', '-q', '--rootdir=.', '--confcutdir=.',
                         '-p', 'no:cacheprovider', f'--junitxml=../logs/{name}.xml', f'checks/test_{name}.py'])

    def execute(self, root, command, *, junit=None, inputs=None):
        index = len(self.runs) + 1
        before = source_snapshot(root, fresh=True, deadline=self.deadline)
        explicit_tree = tree_hash(root, inputs) if inputs is not None else None
        environment = {**os.environ, 'PYTEST_ADDOPTS': '', 'PYTEST_PLUGINS': '',
                       'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PYTHONNOUSERSITE': '1',
                       'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(root)}
        code, output = None, 'producer input coverage incomplete; command not launched'
        started = time.monotonic()
        if before[0].complete and self.deadline > started:
            try:
                done = run(command, cwd=root, timeout=min(20, self.deadline - started), env=environment)
                code, output = done.returncode, done.stdout + done.stderr
            except (OSError, subprocess.SubprocessError) as error:
                output = str(error)
        records = parse(command, output, code, root, snapshot=before)
        after = source_snapshot(root, fresh=True, deadline=self.deadline)
        moved = not after[0].complete or after[1] != before[1]
        for record in records:
            if code is None or moved:
                record.execution = 'incomplete'; record.result = Result.ERROR
            if inputs is not None:
                # A separate controller-owned scoped producer, not a claim that
                # native receipts automatically gain narrower attribution.
                record.observed = list(inputs); record.scope = ''; record.tree = explicit_tree
                record.run = 'milestone-control-declared-inputs'
                if tree_hash(root, inputs) != explicit_tree:
                    record.execution = 'incomplete'; record.result = Result.ERROR
        ledger = Ledger.load(root)
        ledger.add(records); ledger.save()
        log = self.logs / f'{index:03d}.txt'
        _put(self.directory, log.relative_to(self.directory), output)
        suites = [r for r in records if r.kind is Kind.SUITE]
        assertion_failures, setup_errors = 0, 0
        if junit is not None and code is not None:
            path = self.logs / f'{junit}.xml'
            if path.is_file():
                data = path.read_bytes()
                write(self.logs / f'{index:03d}.xml', data.decode('utf-8'))
                try:
                    xml = ET.fromstring(data)
                    assertion_failures = len(xml.findall('.//failure'))
                    setup_errors = len(xml.findall('.//error'))
                except ET.ParseError:
                    setup_errors = 1
            else:
                setup_errors = 1
        elif code is not None:
            # Real Node 22 TAP diagnostics were probed before this predicate.
            assertion_failures = int('ERR_ASSERTION' in output)
        info = {'command': command, 'exit_code': code, 'elapsed_ms': round((time.monotonic() - started) * 1000, 3),
                'source_fingerprint': before[1], 'source_changed_during_execution': moved,
                'scope': 'controller-declared inputs' if inputs is not None else 'native source scope',
                'output': log.relative_to(self.directory).as_posix(),
                'output_sha256': hashlib.sha256(output.encode()).hexdigest(),
                'testcase_failures': assertion_failures, 'setup_errors': setup_errors,
                'qualified_pass': code == 0 and not moved and not setup_errors and any(r.counted and r.passed > 0 and r.failed == 0 for r in suites),
                'qualified_failure': code is not None and code != 0 and not moved and not setup_errors
                                     and assertion_failures > 0 and any(r.counted and r.failed > 0 for r in suites)}
        self.runs.append(info)
        return info


def _definition(root, rows):
    _put(root, 'elevenpowers.milestones.json', json.dumps({'schema': 1, 'milestones': rows}, indent=2))


def _row(name, inputs, command):
    return {'id': name, 'description': 'Integer-tick expiry denies requests at and after the boundary.',
            'inputs': inputs, 'checks': [{'kind': 'test_suite', 'command': command}]}


def exercise(destination):
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('exercise destination must be a new disposable directory')
    destination.mkdir(parents=True)
    destination = destination.resolve()
    producer = Producer(destination)
    root = destination / 'service'; root.mkdir()
    rows = [_row('provider', ['provider.py', 'checks/test_provider.py'], producer.python('provider')),
            _row('checkout', ['provider.py', 'consumer.py', 'checks/test_checkout.py'], producer.python('checkout')),
            _row('worker', ['provider.py', 'consumer.py', 'worker.py', 'checks/test_worker.py'], producer.python('worker'))]
    _definition(root, rows)
    stages = []
    for name, source in [('provider', PROVIDER), ('checkout', CONSUMER), ('worker', WORKER)]:
        file = {'provider': 'provider.py', 'checkout': 'consumer.py', 'worker': 'worker.py'}[name]
        _put(root, file, source); _put(root, f'checks/test_{name}.py', CHECKS[name])
        Ledger(root=root, task=f'stage-{name}').save()
        current = producer.execute(root, producer.python(name), junit=name)
        initial = build(root)
        refresh = []
        for previous in [r['id'] for r in rows[:len(stages)]]:
            refresh.append(producer.execute(root, producer.python(previous), junit=previous))
        stages.append({'name': name, 'new_check': current, 'before_refresh': initial,
                       'refreshes': refresh, 'after_refresh': build(root)})
    frozen = {name: hashlib.sha256((root / f'checks/test_{name}.py').read_bytes()).hexdigest() for name in CHECKS}
    Ledger(root=root, task='later-change', touched=['provider.py']).save()
    new_task = Ledger.load(root)
    retained = not new_task.evidence and len(new_task.milestone_history['receipts']) == 3
    _put(root, 'provider.py', FAULT)
    after_edit = build(root, impact=True, changed=['provider.py'])
    fault = producer.execute(root, producer.python('checkout'), junit='checkout')
    worker_fault = producer.execute(root, producer.python('worker'), junit='worker')
    after_failed = build(root)
    _put(root, 'provider.py', PROVIDER)
    repaired = [producer.execute(root, producer.python(name), junit=name) for name in CHECKS]
    after_repair = build(root)
    _put(root, 'provider.py', EQUIVALENT)
    equivalent = [producer.execute(root, producer.python(name), junit=name) for name in CHECKS]
    after_equivalent = build(root)
    _put(root, 'unrelated.py', 'unrelated = 1\n')
    broad_unrelated = build(root)
    scoped = destination / 'scoped'; scoped.mkdir()
    _put(scoped, 'provider.py', PROVIDER); _put(scoped, 'checks/test_provider.py', CHECKS['provider'])
    _definition(scoped, [_row('provider', ['provider.py', 'checks/test_provider.py'], producer.python('provider'))])
    explicit_inputs = ['elevenpowers.milestones.json', 'provider.py', 'checks/test_provider.py']
    scoped_run = producer.execute(scoped, producer.python('provider'), junit='provider', inputs=explicit_inputs)
    _put(scoped, 'unrelated.py', 'unrelated = 1\n')
    scoped_unrelated = build(scoped)
    checks_unchanged = all(hashlib.sha256((root / f'checks/test_{name}.py').read_bytes()).hexdigest() == digest
                           for name, digest in frozen.items())
    result = {'schema': 1, 'environment': {'python': sys.version, 'platform': platform.platform()},
              'stages': stages, 'new_task_kept_evidence': retained, 'after_edit': after_edit,
              'fault': fault, 'worker_fault': worker_fault, 'after_failed_refresh': after_failed,
              'repair': repaired[-1], 'repair_checks': repaired, 'after_repair': after_repair,
              'equivalent': equivalent[-1], 'equivalent_checks': equivalent, 'after_equivalent': after_equivalent,
              'native_after_unrelated': broad_unrelated, 'scoped_run': scoped_run,
              'scoped_unrelated': scoped_unrelated, 'frozen_check_sha256': frozen,
              'checks_unchanged': checks_unchanged,
              'limits': ['Authored local capability controls; not a model comparison, installed-host acceptance or coding-benefit measurement.',
                         'Native whole-source receipts conservatively expire on unrelated edits; explicit-scope controls use a separate controller producer.',
                         'Controller-owned expectations cover the stated integer-tick boundary, not arbitrary systems or inputs.']}
    node = shutil.which('node')
    result['node'] = {'state': 'unavailable', 'reason': 'Node executable unavailable'}
    if node:
        version = run(_command([node, '--version']), cwd=destination, timeout=5)
        result['environment']['node'] = version.stdout.strip() if version.returncode == 0 else 'version unavailable'
        js = destination / 'client'; js.mkdir()
        good = 'export function allowed(tick, expiry) { return tick < expiry; }\n'
        bad = 'export function allowed(tick, expiry) { return tick <= expiry; }\n'
        tests = "import test from 'node:test'; import assert from 'node:assert/strict'; import {allowed} from '../lib/rules.mjs';\ntest('before expiry',()=>assert.equal(allowed(9,10),true));\ntest('expiry boundary',()=>assert.equal(allowed(10,10),false));\n"
        _put(js, 'lib/rules.mjs', good); _put(js, 'spec/rules.test.mjs', tests)
        command = _command([node, '--test', 'spec/rules.test.mjs'])
        _definition(js, [_row('entitlement', ['lib/rules.mjs', 'spec/rules.test.mjs'], command)])
        baseline = producer.execute(js, command)
        before = build(js)
        Ledger(root=js, task='later-js').save()
        _put(js, 'lib/rules.mjs', bad)
        expired = build(js)
        rejected = producer.execute(js, command)
        failed = build(js)
        _put(js, 'lib/rules.mjs', good)
        restored = producer.execute(js, command)
        final = build(js)
        result['node'] = {'state': 'exercised', 'baseline': baseline, 'before_edit': before,
                          'after_edit': expired, 'fault': rejected, 'after_failed_refresh': failed,
                          'repair': restored, 'after_repair': final,
                          'qualified': baseline['qualified_pass'] and rejected['qualified_failure']
                                       and restored['qualified_pass'] and final['state'] == 'CURRENT'}
    result['runs'] = producer.runs
    result['qualified'] = (retained and checks_unchanged and fault['qualified_failure'] and worker_fault['qualified_failure']
                           and all(r['qualified_pass'] for r in [*repaired, *equivalent, scoped_run])
                           and after_edit['state'] == 'STALE' and after_failed['state'] == 'FAILED'
                           and after_repair['state'] == 'CURRENT' and scoped_unrelated['state'] == 'CURRENT'
                           and all(r['new_check']['qualified_pass'] and all(x['qualified_pass'] for x in r['refreshes']) for r in stages)
                           and (not node or result['node']['qualified']))
    write(destination / 'observations.json', json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='new disposable directory')
    args = parser.parse_args()
    try:
        value = exercise(args.output)
        print(json.dumps({'qualified': value['qualified'], 'producer_runs': len(value['runs']),
                          'node': value['node']['state'], 'output': str(args.output)}, indent=2))
        return 0 if value['qualified'] else 1
    except (OSError, ValueError) as error:
        parser.exit(2, f'Exercise failed: {error}\n')


if __name__ == '__main__':
    sys.exit(main())
