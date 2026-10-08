"""Read-only, unsigned verification reports for any host or project."""
from datetime import datetime, timezone
import html
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

from .evidence import freshness_view
from .hosts.edits import coverage as edit_coverage
from .ledger import Ledger, Status
from .redact import scrub_values
from .report import _hint

MAX_RECEIPTS = 1024


def _revision(root, deadline):
    repository = next((p for p in (root, *root.parents) if (p / '.git').exists()), None)
    if repository is None:
        return '', 'no repository', []
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return '', 'unavailable', ['report deadline reached before revision lookup']
    try:
        if repository != root:
            ignored = subprocess.run(['git', '-c', f'safe.directory={repository.as_posix()}',
                                      'check-ignore', '-q', '.'], cwd=root, capture_output=True,
                                     timeout=min(5, remaining))
            if ignored.returncode == 0:
                return '', 'no repository', []  # Independent ignored scratch project.
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return '', 'unavailable', ['report deadline reached before revision lookup']
        done = subprocess.run(['git', '-c', f'safe.directory={repository.as_posix()}',
                               'rev-parse', '--verify', 'HEAD'], cwd=root, capture_output=True,
                              text=True, timeout=min(5, remaining))
        revision = done.stdout.strip()
        if done.returncode == 0 and re.fullmatch(r'[0-9a-fA-F]{40,64}', revision):
            return revision, 'available', []
    except (OSError, subprocess.SubprocessError):
        pass
    return '', 'unavailable', ['Git revision unavailable (including an unborn repository)']


def _portable(value, root):
    value = scrub_values(value)
    if isinstance(value, str):
        return value.replace(str(root), '<project>').replace(root.as_posix(), '<project>')
    if isinstance(value, list):
        return [_portable(item, root) for item in value]
    if isinstance(value, dict):
        return {key: _portable(item, root) for key, item in value.items()}
    return value


def build(root: Path, *, timeout=120):
    started = time.monotonic()
    deadline = time.monotonic() + timeout
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('project must be a directory')
    if not math.isfinite(timeout) or timeout < 0 or timeout > 600:
        raise ValueError('report timeout must be between 0 and 600 seconds')
    ledger = Ledger.load(root)
    pending, gaps = edit_coverage(root, ledger.task)
    latest = {}
    for receipt in ledger.evidence:
        key = receipt.kind, receipt.identity
        if key not in latest or receipt.at >= latest[key].at:
            latest[key] = receipt
    records = sorted(latest.values(), key=lambda receipt: receipt.at)
    omitted = max(0, len(records) - MAX_RECEIPTS)
    records = records[-MAX_RECEIPTS:]
    actions, receipts, claims = [], [], []
    scan_started = time.monotonic()
    with freshness_view(root, deadline=deadline) as (scan, fingerprint):
        scan_ms = (time.monotonic() - scan_started) * 1000
        for record in records:
            if time.monotonic() >= deadline:
                scan.issues.append('report deadline reached processing receipts')
                omitted += len(records) - len(receipts)
                break
            fresh = record.freshness(root)
            from .hosts.readiness import receipt_key
            receipts.append({'kind': record.kind.value, 'identity': record.identity,
                             'receipt_key': receipt_key(record), 'declaration': record.declaration,
                             'command': record.command, 'result': record.result.value,
                             'declared_command': record.declared_command,
                             'execution': record.execution, 'freshness': fresh.value,
                             'recorded_at': record.at, 'scope': record.scope or 'explicit paths',
                             'observed_files': len(record.observed), 'fingerprint': record.tree,
                             'coverage_issues': list(record.coverage_issues),
                             'passed': record.passed, 'failed': record.failed, 'counted': record.counted})
            if record.execution != 'complete':
                actions.append(f'Complete the incomplete command: {record.command or record.identity}')
            elif record.result.value != 'pass':
                actions.append(f'Inspect the failed command: {record.command or record.identity}')
            elif fresh.value != 'fresh':
                actions.append(f'Rerun the stale command: {record.command or record.identity}')
        try:
            verdicts = ledger.verdicts() if time.monotonic() < deadline else []
        except TimeoutError:
            scan.issues.append('report deadline reached evaluating obligations')
            verdicts = []
        for verdict in verdicts:
            checks = []
            for check in verdict.checks:
                checks.append({'obligation': check.obligation.description, 'met': check.met,
                               'freshness': check.freshness.value if check.freshness else None,
                               'evidence': check.evidence.identity if check.evidence else None,
                               'caveat': check.caveat})
                if not check.met:
                    actions.append(_hint(ledger, check))
                elif check.freshness and check.freshness.value != 'fresh':
                    actions.append('Rerun evidence for: ' + check.obligation.description)
            claims.append({'claim': verdict.claim.value, 'state': verdict.status.value, 'checks': checks})
        order = [Status.CONTRADICTED, Status.UNVERIFIED, Status.STALE, Status.VERIFIED]
        status = min((v.status for v in verdicts), key=order.index).value if verdicts else Status.UNVERIFIED.value
    issues = list(scan.issues)
    from .strength.view import view as strength_view
    strength = strength_view(root, ledger.task, ledger.config, fingerprint, deadline)
    strength['issues'] += [d['why'] for d in ledger.decisions if d.get('what') == 'test strength incomplete']
    revision, revision_state, revision_issues = _revision(root, deadline)
    issues += revision_issues
    milestones = None
    from .milestones.definition import configured as milestones_configured
    if milestones_configured(root):
        from .milestones import build as milestone_report
        milestones = milestone_report(root, seconds=max(0, min(30, deadline - time.monotonic())))
    if time.monotonic() >= deadline:
        issues.append('report deadline reached; report coverage is incomplete')
    issues += [d['why'] for d in ledger.decisions if d.get('what') == 'unattributed native edit']
    if pending or gaps:
        issues.append(f'Native edit coverage incomplete: {pending} pending callbacks; {gaps} evicted baselines')
    if omitted:
        issues.append(f'{omitted} latest receipts omitted because the report budget was exceeded')
    complete = not issues
    if not complete and status != Status.CONTRADICTED.value:
        status = Status.UNVERIFIED.value
    if not ledger.claims:
        actions.insert(0, 'No active task claim is recorded; execution receipts do not certify completed work.')
    if issues:
        actions.insert(0, 'Resolve incomplete source/edit/report coverage before relying on verification.')
    value = {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
             'project': {'name': root.name, 'revision': revision, 'revision_state': revision_state},
             'state': status, 'task': {'id': ledger.task, 'risk': ledger.risk.value,
                                     'touched': list(ledger.touched), 'claims': claims},
             'coverage': {'complete': complete, 'issues': issues, 'selected_files': len(scan.files),
                          'source_complete': scan.complete, 'source_issues': list(scan.issues),
                          'selected_bytes': scan.bytes, 'source_fingerprint': fingerprint,
                          'latest_receipts_total': len(latest), 'omitted_receipts': omitted},
             'commands': dict(ledger.config.commands), 'receipts': receipts,
             'test_strength': strength,
             'timings': {'source_snapshot_ms': round(scan_ms, 3),
                         'report_ms': round((time.monotonic() - started) * 1000, 3)},
             'next_actions': list(dict.fromkeys(actions)),
             'limits': ['Unsigned local observation, not independent attestation or an improved patch-outcome claim.',
                        'Input freshness is evaluated at report creation; later edits require a new report.',
                        'The deadline is cooperative; an in-flight filesystem read can finish after it, then coverage is incomplete.',
                        'Target observations cannot prove absence of unrelated side effects or identify competing writers.',
                        'Prompts, transcripts, captured outputs and receipt details are excluded.']}
    if milestones is not None:
        value['milestones'] = milestones
    return _portable(value, root)


def _text(value):
    literal = re.sub(r'([\\`*_{}\[\]()#+\-.!|~>])', r'\\\1', str(value))
    return html.escape(literal, quote=False).replace('\r', '').replace('\n', '<br>')


def markdown(value):
    project, task, coverage = value['project'], value['task'], value['coverage']
    lines = ['# ElevenPowers verification report', '',
             f"Project: {_text(project['name'])} · Revision: {_text(project['revision'] or project['revision_state'])}",
             f"Generated: {_text(value['generated_at'])}", '', f"**Task verification: {_text(value['state'])}**",
             f"Source/report coverage: {'complete' if coverage['complete'] else 'incomplete'}; {coverage['selected_files']} selected files, {coverage['selected_bytes']} bytes.",
             '', '## Claims and obligations', '']
    for claim in task['claims']:
        lines.append(f"- {_text(claim['claim'])}: {_text(claim['state'])}")
        for check in claim['checks']:
            state = check['freshness'] if check['met'] else 'missing'
            lines.append(f"  - {_text(check['obligation'])}: {_text(state or 'met')}; evidence {_text(check['evidence'] or 'none')}")
            if check['caveat']:
                lines.append(f"    Qualification: {_text(check['caveat'])}")
    if not task['claims']:
        lines.append('No active claim is recorded; passing commands do not certify completed work.')
    lines += ['', '## Latest execution receipts', '', '| Command / identity | Result | Execution | Source freshness | Observed files |',
              '|---|---|---|---|---|']
    for receipt in value['receipts']:
        cells = [receipt['command'] or receipt['identity'], receipt['result'], receipt['execution'], receipt['freshness'], receipt['observed_files']]
        lines.append('| ' + ' | '.join(_text(cell) for cell in cells) + ' |')
    if not value['receipts']:
        lines.append('| No receipts recorded | — | — | — | — |')
    strength = value.get('test_strength', {})
    lines += ['', '## Changed-code test strength (informational)', '',
              f"Saved analysis: {_text(strength.get('state', 'not_recorded'))}; input freshness: {_text(strength.get('freshness', 'unknown'))}.",
              'Undetected changes are possible test gaps, including equivalent behavior; they do not change the task verdict.']
    if strength.get('baseline'):
        lines.append(f"Baseline: {_text(strength['baseline'])}; attempts: {_text(strength.get('attempts', 0))}.")
    if strength.get('command'):
        lines.append('Analyzed command: ' + _text(strength['command']))
    if strength.get('command_coverage',{}).get('scope')=='recorded_command_only':
        lines.append('Only the analyzed command was observed; other test commands may detect these changes.')
    selection=strength.get('selection',{})
    if selection.get('strategy')=='changed_functions_and_hunks':
        lines.append('Sampling targets changed lines and their enclosing functions; it is not exhaustive coverage.')
    elif selection.get('strategy')=='legacy_whole_files':
        lines.append('Legacy sampling covers whole changed files without attribution to edited functions.')
    if strength.get('summary'):
        lines.append(', '.join(f'{_text(key)}: {_text(count)}' for key, count in strength['summary'].items()))
    lines += ['- ' + _text(issue) for issue in strength.get('issues', [])]
    if strength.get('observations'):
        lines += ['', '| Changed source | Line | Mutation operator | Observation | Relation to edit | Context |', '|---|---|---|---|---|---|']
        for observation in strength['observations']:
            relation={'changed_lines':'changed lines','changed_function':'enclosing changed function',
                      'deletion_context':'deletion context','legacy_whole_file':'legacy whole-file sample'}.get(observation.get('relevance'),'unqualified')
            line = str(observation['line'])
            if observation.get('end_line', observation['line']) != observation['line']:
                line += '–' + str(observation['end_line'])
            cells=[observation['path'], line, observation['operator'], observation['status'],
                   relation, observation.get('context','') or '—']
            lines.append('| ' + ' | '.join(_text(cell) for cell in cells) + ' |')
    lines += ['- ' + _text(limit) for limit in strength.get('limitations', [])]
    if 'milestones' in value:
        from .milestones import markdown as milestone_markdown
        lines += ['', '## Behavior evidence across milestones', '', *milestone_markdown(value['milestones']).splitlines()[2:]]
    lines += ['', '## Changed targets', '']
    lines += ['- ' + _text(path) for path in task['touched']] or ['No edited targets recorded.']
    lines += ['', '## Coverage and next actions', '']
    lines += ['- ' + _text(issue) for issue in coverage['issues']]
    lines += ['- ' + _text(action) for action in value['next_actions']] or ['No missing action identified by the recorded claims.']
    lines += ['', '## Evidence limits', '', *['- ' + _text(limit) for limit in value['limits']], '']
    return '\n'.join(lines)


def write(path: Path, text: str, *, force=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.ep-report-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if force:
            os.replace(name, path)
        else:
            os.link(name, path)  # Atomic no-overwrite publication, including concurrent writers.
    finally:
        if os.path.exists(name):
            os.unlink(name)
