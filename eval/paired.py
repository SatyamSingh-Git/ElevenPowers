"""Explicit bounded subscription pilot with immutable per-run records."""
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import re
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
        record['observation'] = subscription.observation(host, result.stdout, result.stderr)
        record['contract_unchanged'] = (challenge.contract(root) and sealed == _seal(root, host, arm) and
                                        challenge.identity() == record['identity'] and
                                        fingerprint(source) == record['runtime_fingerprint'] and
                                        record_path.read_bytes() == initial)
        if not record['contract_unchanged']:
            record['state'] = 'invalid'
        elif result.returncode or not record['observation']['completed'] or record['observation']['failure'] == 'blocked_by_policy' or (
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


def _protocol(protocol):
    try:
        fields = {'schema_version', 'identity', 'models', 'effort', 'seconds_per_run', 'schedule', 'runtime_fingerprint'}
        if (not isinstance(protocol, dict) or set(protocol) != fields or
                type(protocol['schema_version']) is not int or protocol['schema_version'] != 1 or
                protocol['models'] != subscription.MODELS or protocol['effort'] != 'medium' or
                set(protocol['identity']) != {'task', 'prompt', 'grader'} or
                any(not isinstance(v, str) or not re.fullmatch('[a-f0-9]{64}', v) for v in protocol['identity'].values()) or
                not isinstance(protocol['runtime_fingerprint'], str) or not re.fullmatch('[a-f0-9]{64}', protocol['runtime_fingerprint']) or
                type(protocol['seconds_per_run']) not in (int, float) or not math.isfinite(protocol['seconds_per_run']) or
                not 0 < protocol['seconds_per_run'] <= 240 or
                not isinstance(protocol['schedule'], list) or len(protocol['schedule']) != 8 or
                any(not isinstance(v, (list, tuple)) or len(v) != 3 or type(v[1]) is not int for v in protocol['schedule']) or
                [tuple(v) for v in protocol['schedule']] != schedule()):
            raise ValueError('invalid recorded pilot protocol')
    except (TypeError, AttributeError, KeyError) as exc:
        raise ValueError('malformed recorded pilot protocol') from exc


def _private_fields(record, required):
    if set(record) - required - {'error'}:
        raise ValueError('unknown pilot record fields')
    if 'error' in record and record['error'] not in ('OSError', 'ValueError', 'FileNotFoundError',
            'PermissionError', 'SubprocessError', 'OutputLimitExceeded'):
        raise ValueError('unsupported pilot error metadata')
    try:
        date = datetime.fromisoformat(record['generated_at'])
        if date.tzinfo is None:
            raise ValueError('pilot time must include timezone')
        observation = record['observation']
        if observation is not None:
            if (not isinstance(observation, dict) or set(observation) - {'completed', 'usage', 'models', 'completion_language', 'failure'} or
                    type(observation.get('completed')) is not bool or type(observation.get('completion_language')) is not bool or
                    not isinstance(observation.get('models'), list) or len(observation['models']) > 4 or
                    any(model not in subscription.MODELS.values() for model in observation['models']) or
                    observation.get('failure', 'unavailable') not in ('unavailable', 'quota_exhausted', 'blocked_by_policy')):
                raise ValueError('unsupported pilot observation')
            usage = observation.get('usage')
            if usage is not None and (not isinstance(usage, dict) or set(usage) - {
                    'input_tokens', 'output_tokens', 'cached_input_tokens', 'cache_read_input_tokens',
                    'cache_creation_input_tokens', 'reasoning_output_tokens'} or
                    any(type(n) is not int or not 0 <= n <= 1_000_000_000 for n in usage.values())):
                raise ValueError('unsupported pilot usage metadata')
        grade = record['grade']
        if grade is not None and (not isinstance(grade, dict) or set(grade) != {'state', 'passed', 'total', 'regressions', 'checks'}):
            raise ValueError('unknown grade fields')
        mechanisms = record['mechanisms']
        if not isinstance(mechanisms, dict) or set(mechanisms) - {'pipeline_health', 'task_verification', 'callbacks', 'receipt_outcomes', 'coverage_complete'}:
            raise ValueError('unknown mechanism fields')
        if mechanisms:
            if (mechanisms.get('pipeline_health') not in ('waiting', 'attention', 'incomplete', 'observed') or
                    mechanisms.get('task_verification') not in ('VERIFIED', 'UNVERIFIED', 'STALE', 'CONTRADICTED') or
                    type(mechanisms.get('coverage_complete')) is not bool):
                raise ValueError('invalid mechanism state')
            for key, names in [('callbacks', ('SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'Stop')),
                               ('receipt_outcomes', ('pass', 'fail'))]:
                counts = mechanisms.get(key)
                if (not isinstance(counts, dict) or set(counts) != set(names) or
                        any(type(n) is not int or not 0 <= n <= 1_000_000_000 for n in counts.values())):
                    raise ValueError('invalid mechanism counts')
    except (TypeError, AttributeError, KeyError) as exc:
        raise ValueError('malformed pilot metadata') from exc


def summarize(records, protocol=None):
    if not isinstance(records, list) or len(records) > 8:
        raise ValueError('pilot accepts at most eight records')
    if protocol is not None:
        _protocol(protocol)
    expected_identity = protocol['identity'] if protocol else challenge.identity()
    states = ('resolved', 'unresolved', 'regressed', 'invalid', 'setup', 'timeout', 'host_failed', 'running')
    for record in records:
        required = {'schema_version', 'host', 'arm', 'replicate', 'state', 'model', 'effort', 'budget_seconds',
                    'generated_at', 'identity', 'runtime_fingerprint', 'elapsed_ms', 'exit_code',
                    'observation', 'grade', 'mechanisms', 'contract_unchanged'}
        if (not isinstance(record, dict) or record.get('host') not in subscription.MODELS or
                not required.issubset(record) or type(record.get('schema_version')) is not int or record['schema_version'] != 1 or
                record.get('arm') not in ('baseline', 'tool') or record.get('state') not in states or
                type(record.get('replicate')) is not int or record['replicate'] not in (0, 1) or
                record.get('model') != subscription.MODELS[record['host']] or record.get('effort') != 'medium' or
                record.get('identity') != expected_identity or
                not isinstance(record.get('runtime_fingerprint'), str) or not re.fullmatch('[a-f0-9]{64}', record['runtime_fingerprint']) or
                type(record.get('budget_seconds')) not in (int, float) or not math.isfinite(record['budget_seconds']) or
                not 0 < record['budget_seconds'] <= 240 or type(record.get('contract_unchanged')) is not bool):
            raise ValueError('invalid or conflicting pilot record')
        _private_fields(record, required)
        if protocol and (record['runtime_fingerprint'] != protocol['runtime_fingerprint'] or
                         record['budget_seconds'] != protocol['seconds_per_run']):
            raise ValueError('record conflicts with recorded pilot protocol')
        if record['elapsed_ms'] is not None and (type(record['elapsed_ms']) not in (int, float) or
                                                not math.isfinite(record['elapsed_ms']) or record['elapsed_ms'] < 0):
            raise ValueError('invalid pilot timing')
        if record['state'] in ('resolved', 'unresolved', 'regressed'):
            from .challenge_grader import CHECK_NAMES
            grade, observation = record['grade'], record['observation']
            if (not isinstance(grade, dict) or grade.get('state') != 'graded' or
                    type(grade.get('total')) is not int or grade['total'] != 16 or
                    not isinstance(grade.get('checks'), dict) or set(grade['checks']) != set(CHECK_NAMES) or
                    any(type(v) is not bool for v in grade['checks'].values()) or
                    type(grade.get('passed')) is not int or grade['passed'] != sum(grade['checks'].values()) or
                    type(grade.get('regressions')) is not int or grade['regressions'] !=
                    sum(not grade['checks'][k] for k in ('view_total', 'view_statement', 'basic_transfer', 'empty')) or
                    record['contract_unchanged'] is not True or type(record['exit_code']) is not int or record['exit_code'] != 0 or
                    not isinstance(observation, dict) or observation.get('completed') is not True or
                    observation.get('failure') in ('blocked_by_policy', 'quota_exhausted') or record['elapsed_ms'] is None or
                    (record['host'] == 'claude' and observation.get('models') != [subscription.MODELS['claude']])):
                raise ValueError('unsupported graded pilot result')
            expected = 'resolved' if grade['passed'] == 16 else 'regressed' if grade['regressions'] else 'unresolved'
            if record['state'] != expected:
                raise ValueError('pilot state conflicts with its grade')
    if len({(r['budget_seconds'], r['runtime_fingerprint']) for r in records}) > 1:
        raise ValueError('pilot budgets or runtime identities differ')
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
            'identity': expected_identity, 'current_evaluator': expected_identity == challenge.identity(),
            'arms': arms, 'runs': records,
            'limits': ['Eight-run descriptive pilot; no general or statistically powered causal improvement claim.',
                       'Workspace separation is not a closed-book OS boundary; candidate code runs in a contained process.',
                       'Completion wording is a heuristic, not an independently validated intent classifier.',
                       'A ceiling baseline supplies no increased solve-rate evidence; process and patch outcomes are separate.',
                       'Recorded protocols reproduce saved unsigned results; this neither reruns nor validates an earlier evaluator.']}


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
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--directory', type=Path)
    mode.add_argument('--inspect', type=Path, help='read a saved pilot report without executing candidates or models')
    parser.add_argument('--protocol', type=Path)
    parser.add_argument('--codex')
    parser.add_argument('--claude')
    parser.add_argument('--seconds', type=float)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        if args.inspect:
            from core.hosts.diagnostics import read_json
            if not args.protocol or args.codex or args.claude or args.seconds is not None:
                raise ValueError('--inspect requires --protocol and accepts no model launch options')
            if args.force and not args.output:
                raise ValueError('--force requires --output')
            saved = read_json(args.inspect)
            if not isinstance(saved, dict) or not isinstance(saved.get('runs'), list):
                raise ValueError('missing saved pilot runs')
            value = summarize(saved['runs'], protocol=read_json(args.protocol))
            rendered = json.dumps(value, indent=2, allow_nan=False) + '\n'
            if args.output:
                write(args.output, rendered, force=args.force)
            else:
                print(rendered, end='')
            return 0
        if not args.codex or not args.claude or args.protocol or args.output or args.force:
            raise ValueError('--directory requires --codex/--claude and accepts no archive options')
        value = pilot(args.directory, {'codex': args.codex, 'claude': args.claude}, args.seconds if args.seconds is not None else 240)
        return 0 if value['state'] == 'complete' else 1
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    sys.exit(main())
