"""Read-only staged integration diagnostics, independent of task certification."""
import importlib.metadata
import json
import math
from pathlib import Path
import shutil
import sys
import time

from . import export, jobs
from .config import load
from .hosts.doctor import report as configuration_report
from .hosts.readiness import activation, identity
from .hosts.setup import config_path
from .redact import scrub_values

LIMITS = [
    'Local callback observations are not sender authentication or independent attestation.',
    'Pipeline health and task verification are separate; startup alone does not establish end-to-end delivery.',
    'Timings describe the retained sample, not an improvement or a guarantee of future latency.',
    'No project checks, host session or mutation engine are executed by this read-only view.',
    'Freshness is checked at read time under a cooperative deadline; later edits require another read.',
]


def _stamp(root, host):
    paths = [root / '.elevenpowers' / name for name in
             ('ledger.json', 'integrations.json', 'verification.json', 'config.json', 'strength.json',
              'hosts.json', 'patches.json', 'advice.json')]
    paths.append(config_path(host, root))
    paths.append(root / 'elevenpowers.milestones.json')
    result = []
    for path in paths:
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root and root in p.parents):
            raise ValueError('linked project state is unsupported')
        if not path.resolve().is_relative_to(root):
            raise ValueError('project state escapes root')
        try:
            stat = path.stat()
            if stat.st_size > 8 * 1024 * 1024:
                raise ValueError('saved project state exceeds health read limit')
            result.append((stat.st_mtime_ns, stat.st_size))
        except FileNotFoundError:
            result.append(None)
    return result


def _summary(samples):
    values = sorted(float(v) for v in samples
                    if type(v) in (int, float) and math.isfinite(v) and v >= 0)
    if not values:
        return {'samples': 0, 'median_ms': None, 'p95_ms': None}
    n = len(values)
    return {'samples': n, 'median_ms': round((values[(n-1)//2] + values[n//2]) / 2, 3),
            'p95_ms': round(values[math.ceil(n * .95) - 1], 3)}


def _configuration(root):
    """Do not let the tolerant runtime loader hide damaged saved settings."""
    from .config import PROFILES
    from .hosts.diagnostics import read_json
    value = read_json(root / '.elevenpowers/config.json', 1024 * 1024)
    if (not isinstance(value, dict) or
            ('profile' in value and value['profile'] not in PROFILES) or
            not isinstance(value.get('commands', {}), dict) or
            any(not isinstance(v, str) for v in value.get('commands', {}).values()) or
            not isinstance(value.get('scan', {}), dict) or
            not isinstance(value.get('strength', {}), dict) or
            type(value.get('auto_detect', True)) is not bool):
        raise ValueError('invalid saved project configuration')
    return load(root)


def _engines(root, config):
    from .strength.settings import settings
    try:
        options = settings(config.strength)
        if not options.enabled:
            return {'state': 'disabled'}
    except (ValueError, TypeError):
        return {'state': 'incomplete', 'reason': 'Invalid optional engine settings'}
    from .hosts.diagnostics import read_json
    try:
        cosmic = {'state': 'unchecked', 'reason': 'selected interpreter was not executed'}
        if not options.python:
            try:
                version = importlib.metadata.version('cosmic-ray')
                cosmic = {'state': 'metadata_present' if version == '8.7.0' else 'unsupported_version', 'version': version}
            except importlib.metadata.PackageNotFoundError:
                cosmic = {'state': 'unavailable'}
        engine = Path(options.stryker) if options.stryker else root / 'node_modules/@stryker-mutator/instrumenter'
        stryker = {'state': 'unavailable'}
        manifest = engine / 'package.json'
        if manifest.exists():
            try:
                version = read_json(manifest, 65536).get('version')
                stryker = {'state': ('runtime_missing' if not shutil.which('node') else
                                    'metadata_present' if version == '9.5.1' else 'unsupported_version'),
                           'version': str(version)[:32]}
            except (ValueError, OSError, TypeError, AttributeError):
                stryker = {'state': 'incomplete', 'reason': 'Stryker package metadata unavailable'}
        return {'state': 'optional', 'cosmic_ray': cosmic, 'stryker': stryker,
                'limit': 'Package metadata is availability information, not an executed engine check.'}
    except (ValueError, OSError, TypeError, AttributeError) as exc:
        return {'state': 'incomplete', 'reason': 'Optional engine metadata unavailable: ' + type(exc).__name__}


def inspect(host, root, timeout=10):
    from .hosts.onboarding import runtime_name, select_host
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 <= timeout <= 120:
        raise ValueError('health seconds must be between 0 and 120')
    started = time.monotonic()
    deadline = started + timeout
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('project must be a directory')
    host = select_host(host, root)
    issues, actions = [], []
    live = {'state': 'unobserved'}
    text, configured, body, config, before = '', False, None, None, None
    try:
        before = _stamp(root, host)
        text, configured = configuration_report(host, root)
        live = activation(host, root)
        config = _configuration(root)
        body = export.build(root, timeout=max(0, deadline - time.monotonic()))
        if _stamp(root, host) != before:
            issues.append('Project diagnostic/evidence state changed during this read; read again.')
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        issues.append('Project diagnostic/evidence state unavailable: ' + type(exc).__name__)
    if body is None:
        body = {'state': 'UNVERIFIED', 'task': {'id': ''}, 'receipts': [], 'commands': {},
                'coverage': {'complete': False, 'issues': [], 'selected_files': 0, 'selected_bytes': 0},
                'test_strength': {'state': 'unavailable'}, 'timings': {}}
    coverage = body['coverage']
    issues.extend(coverage['issues'])
    if time.monotonic() >= deadline:
        issues.append('Health read deadline reached; coverage is incomplete.')
    commands = body['commands']
    runtimes = {name: bool(shutil.which(name)) for command in commands.values() if (name := runtime_name(command))}
    from .parsers import DECLARED_KINDS
    records = [r for r in body['receipts'] if r.get('declaration') in commands and
               (kind := DECLARED_KINDS.get(r['declaration'])) is not None and r['kind'] == kind.value]
    by_need = {}
    def order(r):
        # Equal-time aggregate receipts must never be decided by a passing
        # individual test or by an optimistic incidental output ordering.
        return (r['recorded_at'], r['execution'] != 'complete', r['result'] != 'pass', r['failed'])
    for r in records:
        if r['declaration'] not in by_need or order(r) >= order(by_need[r['declaration']]):
            by_need[r['declaration']] = r
    latest = max(records, key=order, default=None)
    current_task = identity(body['task']['id'])
    phases = live.get('phases', {})
    startup = phases.get('SessionStart', {})
    session = startup.get('session', '')
    unresolved = [name for name, phase in phases.items() if phase.get('last_error') and
                  session and phase.get('session', '') in ('', session) and
                  phase.get('task', '') in ('', current_task) and
                  phase.get('last_at', 0) >= startup.get('last_at', 0)]
    issues.extend(f'Native callback diagnostic {name} failed; retry that phase in the current task/session.'
                  for name in unresolved)
    usable = configured and live.get('state') not in {'configuration-changed', 'removed', 'error'}
    links = [link for link in live.get('receipt_links', []) if usable and
             link.get('task') == current_task and current_task and
             link.get('session') == session and session]
    linked = {link.get('key') for link in links}
    def stage(state, detail):
        return {'state': state, 'detail': detail}
    def observed(phase):
        return bool(usable and session and phase.get('processed') and not phase.get('last_error') and
                    phase.get('session') == session and phase.get('task') == current_task and current_task)
    edits = [p['edit'] for p in phases.values() if p.get('edit', {}).get('changed') and
             usable and session and p['edit'].get('task') == current_task and
             p['edit'].get('session') == session and not p['edit'].get('incomplete')]
    stages = {
        'configuration': stage('observed' if configured else 'attention', text or 'Native configuration unavailable'),
        'environment': stage('observed' if commands and all(runtimes.values()) else 'attention',
                             'Declared runtime lookup only; project dependencies are established by execution'),
        'startup': stage('observed' if usable and startup.get('processed') and session and not startup.get('last_error') else 'waiting',
                         'Processed native startup with session correlation required'),
        'edits': stage('observed' if edits else 'waiting', 'Current-task native edit delivery; target observations do not prove all side effects'),
        'command_capture': stage('observed' if commands and set(by_need) == set(commands) and
                                 all(r.get('receipt_key') in linked for r in by_need.values()) else 'waiting',
                                 'Current receipt must link to this configuration, task and startup session'),
        'completion': stage('observed' if observed(phases.get('Stop', {})) and
                            phases['Stop'].get('last_at', 0) >= max([x['at'] for x in links] +
                            [p.get('last_at', 0) for p in phases.values() if p.get('edit') in edits] + [0]) else 'waiting',
                            'Processed completion in the current task/session required'),
        'report': stage('observed' if coverage['complete'] and not issues else 'incomplete',
                        'Current shared report and input freshness view'),
    }
    needed = list(by_need.values())
    if set(by_need) != set(commands) or not needed:
        verification = 'waiting'
    elif any(r['execution'] != 'complete' or r['coverage_issues'] for r in needed):
        verification = 'incomplete'
    elif any(r['result'] != 'pass' or r['failed'] > 0 for r in needed):
        verification = 'failed'
    elif any(r['freshness'] != 'fresh' for r in needed):
        verification = 'stale'
    elif any(r['counted'] and r['passed'] <= 0 for r in needed):
        verification = 'incomplete'
    else:
        verification = 'observed'
    stages['verification'] = stage(verification, 'Every declared command needs a complete, passing, fresh receipt; not task certification')
    engines = _engines(root, config) if config else {'state': 'incomplete'}
    stages['strength'] = stage(body['test_strength']['state'], 'Optional saved mutation observations; excluded from required pipeline health')
    required = [v['state'] for k, v in stages.items() if k != 'strength']
    status = ('incomplete' if issues or 'incomplete' in required else
              'attention' if any(s in {'attention', 'failed', 'stale', 'gone'} for s in required) else
              'waiting' if 'waiting' in required else 'observed')
    for name, item in stages.items():
        if name != 'strength' and item['state'] != 'observed':
            actions.append(f"{name}: {item['detail']} ({item['state']}).")
    if issues:
        actions.insert(0, 'Resolve diagnostic/coverage issues before relying on the pipeline: ' + '; '.join(issues))
    if live.get('links_evicted'):
        actions.append('Earlier native receipt links were evicted; repeat an acceptance exercise if its history is missing.')
    from .hosts.diagnostics import read_json
    try:
        journal = read_json(root / '.elevenpowers/verification.json', 1024*1024) if not issues else {}
        if not isinstance(journal, dict) or not isinstance(journal.get('checks', []), list):
            raise ValueError('invalid verification journal')
    except (OSError, ValueError):
        journal = {}
        issues.append('Verification progress diagnostics unavailable')
        status = 'incomplete'
    if journal.get('task') == body['task']['id'] and journal.get('status') in ('running', 'incomplete', 'deferred'):
        stages['completion'] = stage('incomplete', 'Verification attempt is running, deferred or interrupted; journal is diagnostic only')
        status = 'incomplete'
    durations = []
    if journal.get('task') == body['task']['id']:
        for check in journal.get('checks', [])[-100:]:
            if isinstance(check, dict) and all(type(check.get(k)) in (int, float) for k in ('started', 'finished')):
                ms = (check['finished'] - check['started']) * 1000
                if math.isfinite(ms) and ms >= 0:
                    durations.append(ms)
    timings = {**body.get('timings', {}), 'health_read_ms': round((time.monotonic() - started) * 1000, 3),
               'callbacks': {name: _summary(phase.get('samples_ms', [])) for name, phase in phases.items()},
               'automatic_commands': _summary(durations[-32:]), 'sample_limit': 32}
    receipt = ({**latest, 'freshness': latest['freshness']} if latest else None)
    value = {'schema_version': 1, 'host': host, 'project': str(root), 'python': sys.version.split()[0],
             'configuration_ok': configured, 'configuration_report': text, 'activation': live,
             'commands': commands, 'runtimes': runtimes, 'profile': config.profile if config else 'unknown',
             'coverage': {'complete': not issues and coverage['complete'], 'files': coverage['selected_files'],
                          'bytes': coverage['selected_bytes'], 'issues': list(dict.fromkeys(issues))},
             'latest_receipt': receipt, 'pending_patches': 0, 'patch_gaps': 0,
             'task_state': body['state'], 'task': body['task']['id'],
             'health': {'state': status, 'stages': stages}, 'test_strength': body['test_strength'],
             'optional_engines': engines, 'timings': timings, 'next_actions': actions, 'limits': LIMITS}
    value['report_coverage'] = coverage
    from .milestones.delivery import inspect as advice_inspect
    value['milestone_advice'] = advice_inspect(root, host, body['task']['id'], live, body['receipts'])
    value['coverage']['complete'] = coverage.get('source_complete', False) and not any('diagnostic' in x.lower() for x in issues)
    value['coverage']['issues'] = list(coverage.get('source_issues', issues))
    from .hosts.edits import coverage as edit_coverage
    try:
        value['pending_patches'], value['patch_gaps'] = edit_coverage(root, body['task']['id'])
        if any(type(value[k]) is not int or not 0 <= value[k] <= 1_000_000_000 for k in ('pending_patches', 'patch_gaps')):
            raise ValueError('invalid native edit diagnostic counts')
    except (OSError, ValueError, TypeError, AttributeError, KeyError):
        value['coverage']['complete'] = False
        value['coverage']['issues'].append('Native edit diagnostic state unavailable')
        value['health']['state'] = 'incomplete'
        value['health']['stages']['report'] = stage('incomplete', 'Native edit diagnostic state unavailable')
        value['next_actions'].insert(0, 'Repair unreadable native edit diagnostic state before relying on coverage.')
    final_issue = ''
    try:
        if _stamp(root, host) != before:
            final_issue = 'Project diagnostic/evidence state changed during this read; read again.'
    except (OSError, ValueError):
        final_issue = 'Project diagnostic/evidence state unavailable at end of read.'
    if time.monotonic() >= deadline:
        final_issue = 'Health read deadline reached; coverage is incomplete.'
    if final_issue:
        value['health']['state'] = 'incomplete'
        value['health']['stages']['report'] = stage('incomplete', final_issue)
        value['coverage']['complete'] = False
        if final_issue not in value['coverage']['issues']:
            value['coverage']['issues'].append(final_issue)
        value['next_actions'].insert(0, final_issue)
    value['timings']['health_read_ms'] = round((time.monotonic() - started) * 1000, 3)
    return scrub_values(value)


def render(value):
    lines = [f"ElevenPowers readiness: {value['host']}", f"Project: {value['project']}",
             f"Pipeline health: {value['health']['state']}; task verification: {value['task_state']}",
             value['configuration_report'], f"Activation: {value['activation']['state']}",
             f"Source coverage: {'complete' if value['coverage']['complete'] else 'incomplete'}; "
             f"{value['coverage']['files']} files, {value['coverage']['bytes']} bytes"]
    lines.extend(f"Stage {name}: {item['state']} — {item['detail']}" for name, item in value['health']['stages'].items())
    lines.extend(f'Command {need}: {command}' for need, command in value['commands'].items())
    lines.extend(f"Runtime {name}: {'available' if found else 'missing on PATH'}" for name, found in value['runtimes'].items())
    receipt = value['latest_receipt']
    lines.append(f"Latest declared run: {receipt['execution']} / {receipt['result']}; {receipt['freshness']}; {receipt['command']}"
                 if receipt else 'Latest declared run: none recorded')
    lines.append(f"Health read: {value['timings']['health_read_ms']} ms; optional engines: {value['optional_engines']['state']}")
    if 'milestone_advice' in value:
        advice = value['milestone_advice']
        lines.append(f"Advice delivery: {advice['state']}; subsequent matching native receipts: "
                     f"{advice['matching_native_receipts']}; model consumption unproven")
        lines.extend('Advice observation: ' + issue for issue in advice['issues'])
    lines.extend('Next action: ' + item for item in value['next_actions'])
    lines.extend('Limit: ' + item for item in value['limits'])
    return '\n'.join(lines)
