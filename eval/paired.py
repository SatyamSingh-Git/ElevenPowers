"""Explicit bounded subscription pilot with immutable per-run records."""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

from core.config import Config, save
from core.export import write
from core.hosts.provenance import fingerprint
from core.hosts.setup import install, config_path
from core.process import run
from . import challenge, subscription


def schedule():
    return [(host, replicate, arm) for replicate in range(2) for host in subscription.MODELS
            for arm in (('baseline', 'tool') if replicate == 0 else ('tool', 'baseline'))]


def _seal(root, host, arm):
    paths = [root / '.elevenpowers/config.json', config_path(host, root)] if arm == 'tool' else []
    return [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]


def run_case(host, arm, root, executable, source=None, timeout=240, replicate=0):
    if host not in subscription.MODELS or arm not in ('baseline', 'tool'):
        raise ValueError('unknown host or arm')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 240:
        raise ValueError('pilot run budget must be within 0–240 seconds')
    if type(replicate) is not int or replicate not in (0, 1):
        raise ValueError('pilot supports two replicates')
    root = Path(root).absolute()
    if root.exists() or root.is_symlink() or any(p.is_symlink() for p in root.parents):
        raise ValueError('pilot requires a new unlinked candidate directory')
    source = Path(source or Path(__file__).resolve().parents[1]).resolve()
    record_path = root.with_name(root.name + '-result.json')
    record = {'schema_version': 1, 'host': host, 'arm': arm, 'replicate': replicate, 'state': 'running',
              'model': subscription.MODELS[host], 'effort': 'medium', 'budget_seconds': timeout,
              'generated_at': datetime.now(timezone.utc).isoformat(), 'identity': challenge.identity(),
              'runtime_fingerprint': fingerprint(source), 'elapsed_ms': None, 'exit_code': None,
              'observation': None, 'grade': None, 'mechanisms': {}, 'contract_unchanged': False}
    write(record_path, json.dumps(record, indent=2))
    initial = record_path.read_bytes()
    started = time.monotonic()
    try:
        challenge.prepare(root)
        if not subscription.auth(host, executable, root):
            raise ValueError('subscription authentication unavailable')
        for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=Pilot', '-c', 'user.email=pilot@example.invalid', 'commit', '-qm', 'Frozen behavioral task']):
            result = run(['git', '-c', f'safe.directory={root.as_posix()}', *args], cwd=root, timeout=15, shell=False)
            if result.returncode:
                raise ValueError('candidate Git setup unavailable')
        if arm == 'tool':
            save(root, Config(profile='guide', commands={'tests': 'python visible.py'}, auto_detect=False,
                              strength={'enabled': False}))
            install(host, root, sys.executable, source)
        sealed = _seal(root, host, arm)
        env = {**os.environ, 'PATH': str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', '')}
        begin = time.monotonic()
        result = run(subscription.command(host, executable, root, challenge.PROMPT), cwd=root,
                     timeout=timeout, shell=False, env=env)
        record['elapsed_ms'] = round((time.monotonic() - begin) * 1000, 3)
        record['exit_code'] = result.returncode
        record['observation'] = subscription.observation(host, result.stdout)
        record['contract_unchanged'] = (challenge.contract(root) and sealed == _seal(root, host, arm) and
                                        challenge.identity() == record['identity'] and
                                        fingerprint(source) == record['runtime_fingerprint'] and
                                        record_path.read_bytes() == initial)
        if not record['contract_unchanged']:
            record['state'] = 'invalid'
        elif result.returncode or not record['observation']['completed'] or (
                host == 'claude' and record['observation']['models'] != [subscription.MODELS[host]]):
            record['state'] = 'host_failed'
        else:
            grade = challenge.grade(root); record['grade'] = grade
            record['state'] = ('setup' if grade['state'] != 'graded' else
                               'resolved' if grade['passed'] == grade['total'] else
                               'regressed' if grade['regressions'] else 'unresolved')
        if arm == 'tool':
            from core import health
            observed = health.inspect(host, root, timeout=10)
            phases = observed['activation'].get('phases', {})
            record['mechanisms'] = {'pipeline_health': observed['health']['state'],
                                    'task_verification': observed['task_state'],
                                    'callbacks': {name: phases.get(name, {}).get('processed', 0) for name in
                                                  ('SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'Stop')},
                                    'receipt_outcomes': {name: sum(link.get('result') == name for link in observed['activation'].get('receipt_links', []))
                                                         for name in ('pass', 'fail')},
                                    'coverage_complete': observed['coverage']['complete']}
    except subprocess.TimeoutExpired:
        record['state'] = 'timeout'
        record['elapsed_ms'] = round((time.monotonic() - started) * 1000, 3)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        record['state'] = 'setup'; record['error'] = type(exc).__name__
    write(record_path, json.dumps(record, indent=2, allow_nan=False), force=True)
    return record


def summarize(records):
    if not isinstance(records, list) or len(records) > 8:
        raise ValueError('pilot accepts at most eight records')
    states = ('resolved', 'unresolved', 'regressed', 'invalid', 'setup', 'timeout', 'host_failed', 'running')
    for record in records:
        if (not isinstance(record, dict) or record.get('host') not in subscription.MODELS or
                record.get('arm') not in ('baseline', 'tool') or record.get('state') not in states or
                type(record.get('replicate')) is not int or record['replicate'] not in (0, 1) or
                record.get('model') != subscription.MODELS[record['host']] or record.get('effort') != 'medium' or
                record.get('identity') != challenge.identity()):
            raise ValueError('invalid or conflicting pilot record')
    unique = [(r['host'], r['arm'], r.get('replicate')) for r in records]
    complete = len(records) == 8 and len(set(unique)) == 8 and all(r['state'] != 'running' for r in records)
    arms = []
    for host in subscription.MODELS:
        for arm in ('baseline', 'tool'):
            selected = [r for r in records if r['host'] == host and r['arm'] == arm]
            arms.append({'host': host, 'arm': arm, 'runs': len(selected),
                         'resolved': sum(r['state'] == 'resolved' for r in selected),
                         'states': {state: sum(r['state'] == state for r in selected) for state in
                                    ('resolved', 'unresolved', 'regressed', 'invalid', 'setup', 'timeout', 'host_failed', 'running')},
                         'completion_language_with_failed_grade': sum(bool((r.get('observation') or {}).get('completion_language')) and
                            bool(r.get('grade')) and r['grade']['passed'] < r['grade']['total'] for r in selected)})
    return {'schema_version': 1, 'kind': 'subscription_pilot', 'state': 'complete' if complete else 'incomplete',
            'identity': challenge.identity(), 'arms': arms, 'runs': records,
            'limits': ['Eight-run descriptive pilot; no general or statistically powered causal improvement claim.',
                       'Workspace separation is not a closed-book OS boundary; candidate code runs in a contained process.',
                       'Completion wording is a heuristic, not an independently validated intent classifier.',
                       'A ceiling baseline supplies no increased solve-rate evidence; process and patch outcomes are separate.']}


def pilot(directory, executables, seconds=240):
    directory = Path(directory).absolute()
    if directory.exists() or directory.is_symlink() or any(p.is_symlink() for p in directory.parents):
        raise ValueError('pilot requires a new unlinked directory')
    if set(executables) != set(subscription.MODELS):
        raise ValueError('both exact subscription hosts required')
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 < seconds <= 240:
        raise ValueError('pilot seconds must be within 0–240')
    directory.mkdir(parents=True)
    protocol = {'schema_version': 1, 'identity': challenge.identity(), 'models': subscription.MODELS,
                'effort': 'medium', 'seconds_per_run': seconds, 'schedule': schedule(),
                'runtime_fingerprint': fingerprint()}
    write(directory / 'protocol.json', json.dumps(protocol, indent=2))
    records = []
    for host, replicate, arm in schedule():
        if protocol['identity'] != challenge.identity() or protocol['runtime_fingerprint'] != fingerprint():
            raise ValueError('frozen software or evaluator changed; stop instead of redesigning the pilot')
        record = run_case(host, arm, directory / f'{host}-{replicate}-{arm}', executables[host],
                          timeout=seconds, replicate=replicate)
        records.append(record)
        write(directory / 'summary.json', json.dumps(summarize(records), indent=2, allow_nan=False), force=True)
        print(f"{host} {arm}: {record['state']}; grade {record.get('grade') and record['grade']['passed']}", flush=True)
    return summarize(records)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--codex', required=True)
    parser.add_argument('--claude', required=True)
    parser.add_argument('--seconds', type=float, default=240)
    args = parser.parse_args()
    try:
        value = pilot(args.directory, {'codex': args.codex, 'claude': args.claude}, args.seconds)
        return 0 if value['state'] == 'complete' else 1
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    sys.exit(main())
