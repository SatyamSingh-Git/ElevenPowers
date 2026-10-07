"""Read-only behavior evidence; CURRENT means a pass within declared scope."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time

from ..evidence import Freshness, Kind, Result, freshness_view
from ..export import _portable, _text
from ..redact import scrub
from .definition import FILE, _pairs, load, safe_path
from .history import read as read_history, record

MAX_LEDGER_BYTES = 8 * 1024 * 1024
STATES = ('INCOMPLETE', 'FAILED', 'STALE', 'ABSENT', 'CURRENT')
LIMITS = [
    'CURRENT is a current passing command within declared observed inputs, not universal behavior correctness.',
    'Expectations and scopes are project assertions; receipts are unsigned local observations, not independent attestation.',
    'Unrecorded dependencies and external environment/services remain unknown.',
    'Source-scoped receipts conservatively expire after unrelated selected-source edits; explicit scopes need all declared inputs.',
    'The deadline is cooperative; bounded observations are not an atomic filesystem transaction.',
    'Inspection runs no project checks, model, installer or host and creates no project state.',
]


def read_ledger(root, deadline):
    path = root / '.elevenpowers' / 'ledger.json'
    try:
        if (path.parent.is_symlink() or path.is_symlink()
                or not path.resolve().is_relative_to(root)):
            raise ValueError('linked or out-of-scope milestone ledger')
        if not path.exists():
            return {}, '', []
        if time.monotonic() >= deadline:
            raise ValueError('milestone deadline reached before ledger read')
        with path.open('rb') as stream:
            data = stream.read(MAX_LEDGER_BYTES + 1)
        if len(data) > MAX_LEDGER_BYTES:
            raise ValueError('milestone ledger exceeds 8 MiB read budget')
        value = json.loads(data.decode('utf-8'), object_pairs_hook=_pairs)
        if not isinstance(value, dict):
            raise ValueError('milestone ledger must be an object')
        return value, hashlib.sha256(data).hexdigest(), []
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError) as error:
        return {}, '', [f'{type(error).__name__}: milestone ledger unavailable: {error}']


def _latest(payload, wanted):
    historical, issues = read_history(payload.get('milestone_history', {}))
    live = payload.get('evidence', [])
    if not isinstance(live, list):
        live = []; issues.append('current ledger receipt inventory is invalid')
    if len(live) > 1024:
        issues.append('current ledger receipt limit reached; older observations omitted')
    records = []
    for value in live[-1024:]:
        try:
            if not isinstance(value, dict):
                raise ValueError('invalid current receipt')
            if (value.get('kind'), value.get('command')) not in wanted:
                continue
            records.append(record(value))
        except (ValueError, TypeError, KeyError, AttributeError):
            issues.append('current ledger contains invalid milestone receipt metadata')
    # The atomic history has already reconciled later entries on timestamp ties.
    latest = {}
    for item in [*records, *historical]:
        key = item.kind.value, item.command
        if key not in latest or item.at >= latest[key].at:
            latest[key] = item
    return latest, list(dict.fromkeys(issues))


def _aggregate(values):
    return min(values, key=STATES.index) if values else 'ABSENT'


def _check(root, check, required, latest, scan, deadline, history_issues):
    item = latest.get((check['kind'], check['command']))
    value = {**check, 'state': 'ABSENT', 'result': None, 'execution': None,
             'freshness': None, 'recorded_at': None, 'scope': None,
             'observed_files': 0, 'receipt_fingerprint': '', 'issues': [],
             'qualifications': ['A passing command supports only its recorded property and declared input scope.']}
    if scrub(check['command']) != check['command']:
        value['issues'].append('redacted command identity cannot establish an exact match')
    if history_issues:
        value['issues'].append('latest milestone receipt history is incomplete or invalid')
    for rel in required:
        try:
            if not safe_path(root, rel).is_file():
                value['issues'].append(f'declared milestone input is missing: {rel}')
        except (OSError, ValueError):
            value['issues'].append(f'declared milestone input is unsafe or unavailable: {rel}')
    if time.monotonic() >= deadline:
        value['issues'].append('milestone deadline reached evaluating check')
    if item is not None:
        value.update(result=item.result.value, execution=item.execution, recorded_at=item.at,
                     scope=item.scope or 'explicit paths', observed_files=len(item.observed),
                     receipt_fingerprint=item.tree)
        if not item.observed or not set(required) <= set(item.observed):
            value['issues'].append('receipt does not cover all declared inputs and the milestone declaration')
        try:
            if time.monotonic() < deadline:
                value['freshness'] = item.freshness(root).value
        except (OSError, ValueError, TimeoutError):
            value['issues'].append('receipt input freshness could not be completed')
        if item.coverage_issues or not scan.complete:
            value['issues'].append('receipt or current source coverage is incomplete')
        if item.scope == 'source' and value['freshness'] == Freshness.FRESH.value:
            if set(item.observed) != set(scan.files):
                value['issues'].append('source receipt inventory disagrees with current source snapshot')
        if item.kind is Kind.SUITE and (not item.ran_tests or
                (item.result is Result.PASS and item.failed > 0)):
            value['issues'].append('test counts are empty or contradict the passing result')
        if item.kind is Kind.SUITE and not item.counted:
            value['qualifications'].append('Opaque command-level result; individual assertions were not counted.')
        if item.execution != 'complete' or item.result is Result.ERROR:
            value['state'] = 'INCOMPLETE'
        elif value['freshness'] not in {Freshness.FRESH.value}:
            value['state'] = 'STALE'
        elif item.result is Result.FAIL:
            value['state'] = 'FAILED'
        else:
            value['state'] = 'CURRENT'
    if value['issues']:
        value['state'] = 'INCOMPLETE'
    value['next_action'] = ('No re-run required by the recorded declared-input evidence.'
                            if value['state'] == 'CURRENT' else f"Run the project-owned check after resolving gaps: {check['command']}")
    return value


def build(root, *, seconds=30, changed=None, impact=False):
    started = time.monotonic()
    if changed is not None and not impact:
        raise ValueError('changed paths require explicitly requested impact advice')
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 <= seconds <= 120:
        raise ValueError('milestone seconds must be finite and between 0 and 120')
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('project must be a directory')
    deadline = started + seconds
    definition = load(root, deadline=deadline)
    value = {'schema': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
             'project': root.name, 'state': 'not_configured', 'milestones': [],
             'coverage': {'complete': True, 'issues': [],
                          'declaration_fingerprint': definition['fingerprint'], 'ledger_fingerprint': ''},
             'impact': {'state': 'not_requested', 'leads': [], 'issues': []},
             'rechecks': {'state': 'not_requested', 'commands': [], 'issues': []},
             'limits': list(LIMITS)}
    if not definition['configured']:
        value['next_actions'] = [f'Declare project-owned behavior in {FILE} to opt in.']
        value['timings'] = {'report_ms': round((time.monotonic() - started) * 1000, 3)}
        return _portable(value, root)
    payload, ledger_fingerprint, issues = read_ledger(root, deadline)
    issues += definition['issues']
    wanted = {(c['kind'], c['command']) for m in definition['milestones'] for c in m['checks']}
    latest, history_issues = _latest(payload, wanted)
    issues += history_issues
    with freshness_view(root, deadline=deadline) as (scan, fingerprint):
        for milestone in definition['milestones']:
            checks = [_check(root, c, [FILE, *milestone['inputs']], latest, scan, deadline,
                             history_issues) for c in milestone['checks']]
            value['milestones'].append({**milestone, 'checks': checks,
                                        'state': _aggregate([c['state'] for c in checks])})
            issues += [i for c in checks for i in c['issues']]
        issues += scan.issues
        value['coverage'].update(source_fingerprint=fingerprint, source_complete=scan.complete,
                                 selected_files=len(scan.files), selected_bytes=scan.bytes)
    if impact:
        from .impact import advise
        impact_started = time.monotonic()
        value['impact'] = advise(root, definition['milestones'],
                                 changed if changed is not None else payload.get('touched', []),
                                 deadline=deadline)
        issues += value['impact']['issues']
        if (value['impact'].get('evidence_source_fingerprint') is not None and
                value['impact']['evidence_source_fingerprint'] != fingerprint):
            message = 'graph and evidence source snapshots disagree; source snapshot moved or coverage differs'
            value['impact']['issues'].append(message)
            value['impact']['state'] = 'incomplete'
            issues.append(message)
        impact_ms = round((time.monotonic() - impact_started) * 1000, 3)
    final_definition = load(root, deadline=deadline)
    _, final_ledger, final_issues = read_ledger(root, deadline)
    issues += final_definition['issues'] + final_issues
    if (final_definition['configured'] != definition['configured'] or
            final_definition['fingerprint'] != definition['fingerprint'] or final_ledger != ledger_fingerprint):
        issues.append('milestone declaration or ledger changed during report collection')
    if time.monotonic() >= deadline:
        issues.append('milestone deadline reached; requested coverage is incomplete')
    issues = list(dict.fromkeys(issues))
    if impact:
        from .rechecks import plan
        value['rechecks'] = plan(value['milestones'], value['impact'], complete=not issues)
        issues = list(dict.fromkeys([*issues, *value['rechecks']['issues']]))
    value['coverage'].update(complete=not issues, issues=issues, ledger_fingerprint=ledger_fingerprint)
    value['state'] = 'INCOMPLETE' if issues else _aggregate([m['state'] for m in value['milestones']])
    value['summary'] = {s: sum(m['state'] == s for m in value['milestones']) for s in STATES}
    value['next_actions'] = list(dict.fromkeys(c['next_action'] for m in value['milestones']
                                             for c in m['checks'] if c['state'] != 'CURRENT'))
    if issues:
        value['next_actions'].insert(0, 'Resolve incomplete declaration, input or history coverage before relying on this view.')
    value['timings'] = {'report_ms': round((time.monotonic() - started) * 1000, 3)}
    if impact:
        value['timings']['impact_ms'] = impact_ms
        value['timings']['report_ms'] = round((time.monotonic() - started) * 1000, 3)
    return _portable(value, root)


def markdown(value):
    lines = ['# ElevenPowers milestone evidence', '', f"**Milestone evidence: {_text(value['state'])}**",
             '', '| Milestone | State | Declared expectation |', '|---|---|---|']
    for item in value['milestones']:
        lines.append('| ' + ' | '.join(_text(item[k]) for k in ('id', 'state', 'description')) + ' |')
    for item in value['milestones']:
        lines += ['', f"## {_text(item['id'])}", '', '| Check | State | Result | Execution | Freshness | Scope |', '|---|---|---|---|---|---|']
        for check in item['checks']:
            lines.append('| ' + ' | '.join(_text(check.get(k) or '—') for k in
                            ('command', 'state', 'result', 'execution', 'freshness', 'scope')) + ' |')
            lines += ['- ' + _text(i) for i in check['issues'] + check['qualifications']]
    if value['impact']['state'] != 'not_requested':
        lines += ['', '## Explained impact leads (informational)', '',
                  'No missing path certifies unaffected behavior or permits excluding fallback checks.']
        for lead in value['impact']['leads']:
            lines.append(f"- {_text(lead['milestone'])}: {_text(lead['input'])} ({_text(lead['category'])})")
            for edge in lead['explanation']:
                lines.append(f"  - {_text(edge['source'])} → {_text(edge['target'])}: {_text(edge['kind'])}")
        lines += ['- ' + _text(i) for i in value['impact']['issues']]
    if value.get('rechecks', {}).get('state') not in (None, 'not_requested'):
        recommendations = value['rechecks']
        lines += ['', '## Recommended recheck order (informational)', '',
                  _text(recommendations['policy']), '',
                  '| Exact command | Kind | Priority | Evidence | Milestones |', '|---|---|---|---|---|']
        for command in recommendations['commands']:
            refs = ', '.join(m['id'] + ': ' + m['state'] for m in command['milestones'])
            lines.append('| ' + ' | '.join(_text(v) for v in (
                command['command'], command['kind'], command['priority'],
                'refresh needed' if command['needs_refresh'] else 'current within recorded scope', refs)) + ' |')
            for reason in command['reasons']:
                lines.append('- ' + _text(f"{reason['milestone']}: {reason['input']} ({reason['category']})"))
            lines += ['- ' + _text(i) for i in command['qualifications'] + command['issues']]
        lines += ['- ' + _text(i) for i in recommendations['issues']]
    lines += ['', '## Coverage and next actions', '']
    lines += ['- ' + _text(i) for i in value['coverage']['issues'] + value['next_actions']]
    lines += ['', '## Limits', '', *['- ' + _text(i) for i in value['limits']], '']
    return '\n'.join(lines)
