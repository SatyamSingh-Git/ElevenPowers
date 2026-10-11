"""Associate an exact committed patch with scoped existing observations."""
import hashlib
import math
import os
from pathlib import Path
import time

from ..export import build as verification_report, _portable
from ..hosts.readiness import receipt_key
from ..ledger import Ledger
from .identity import collect


LIMITS = [
    'Unsigned local evidence, not independent attestation or proof that a patch is safe.',
    'Binding means recorded inputs match the inspected checkout; execution at the requested commit is unknown.',
    'Receipt producer versions, environment and external service freshness are unknown unless separately recorded.',
    'Source selection and explicit scopes do not certify ignored, excluded or unobserved patch inputs.',
    'Before/after reads detect observed changes; they are not an atomic snapshot and cannot detect changes that revert between reads.',
    'No checks, installations or model calls run during reporting. No compatibility or coding-benefit percentage is computed.',
    'Raw diffs, file contents, prompts, transcripts, captured outputs and receipt details are excluded.',
]


def _guard(root, deadline):
    """Bound the state read before the legacy exporter loads the same files."""
    values = []
    for rel, limit in (('.elevenpowers/ledger.json', 8 * 1024 * 1024),
                       ('.elevenpowers/config.json', 1024 * 1024)):
        if time.monotonic() >= deadline:
            raise TimeoutError('bundle deadline reached reading state')
        path = root / rel
        if path.is_symlink() or path.parent.is_symlink():
            raise ValueError('linked evidence state is unsupported')
        if not path.exists():
            values.append(None)
            continue
        with path.open('rb') as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit:
            raise ValueError('evidence state exceeds bundle read budget')
        values.append(hashlib.sha256(raw).hexdigest())
    return values


def _inputs(value):
    return [value['coverage'], value['commands'], value['receipts'], value['task']]


def _check_state(receipt):
    if receipt['execution'] != 'complete':
        return 'incomplete'
    if receipt['result'] != 'pass':
        return 'failed'
    if receipt['freshness'] != 'fresh':
        return 'stale'
    if receipt['counted'] and receipt['passed'] + receipt['failed'] == 0:
        return 'no_tests'
    return 'current'


def build(root, base='HEAD~1', head='HEAD', *, timeout=120):
    """Read an unsigned bundle. Binding is not a task verdict or safety badge."""
    if not math.isfinite(timeout) or not 0 <= timeout <= 600:
        raise ValueError('bundle timeout must be between 0 and 600')
    started = time.monotonic()
    deadline = started + timeout
    root = Path(root).resolve(strict=True)
    patch = collect(root, base, head, seconds=max(0, deadline - time.monotonic()))
    issues = list(patch['issues']) + list(patch['checkout']['issues'])
    report, records = None, {}
    redirects = ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR',
                 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES',
                 'GIT_CONFIG_COUNT', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG')
    if any(name in os.environ for name in redirects):
        issues.append('ambient Git repository/config overrides leave legacy report enumeration unqualified')
    try:
        before = _guard(root, deadline)
        ledger = Ledger.load(root)
        records = {receipt_key(record): record for record in ledger.evidence}
        report = verification_report(root, timeout=max(0, deadline - time.monotonic()))
        check = verification_report(root, timeout=max(0, deadline - time.monotonic()))
        after = _guard(root, deadline)
        if before != after:
            issues.append('ledger or project configuration changed during bundle collection')
        if _inputs(report) != _inputs(check):
            issues.append('observed inputs or receipts changed during bundle collection')
        if not report['coverage']['complete'] or not check['coverage']['complete']:
            issues.append('source, native edit or report coverage is incomplete')
    except (OSError, ValueError, TimeoutError) as exc:
        issues.append(type(exc).__name__ + ': evidence report unavailable or incomplete')
    final = collect(root, base, head, seconds=max(0, deadline - time.monotonic()))
    if patch != final:
        issues.append('patch identity or checkout qualification changed during bundle collection')
    if not final['complete'] or not final['checkout']['eligible']:
        issues += final['issues'] + final['checkout']['issues']
    if time.monotonic() >= deadline:
        issues.append('bundle deadline reached; binding is incomplete')
    bound = patch['complete'] and patch['checkout']['eligible'] and report is not None and not issues
    patch_paths = {change['path'] for change in patch['changes']}
    receipts, covered = [], set()
    for receipt in report['receipts'] if report else []:
        original = records.get(receipt['receipt_key'])
        paths = sorted(patch_paths.intersection(original.observed)) if original else []
        why = []
        if not bound:
            why.append('patch/report binding is unavailable')
        if not original or not original.observed:
            why.append('no recorded input scope is available')
        if not paths:
            why.append('no changed patch path is in the recorded input scope')
        if receipt['freshness'] != 'fresh' or receipt['coverage_issues']:
            why.append('recorded inputs or declaration are stale, gone or incomplete')
        if original and original.scope not in ('', 'source'):
            why.append('unsupported receipt scope')
        associated = not why
        if associated:
            covered.update(paths)
        receipts.append({**receipt, 'association': 'bound' if associated else 'unavailable',
                         'patch_paths': paths, 'association_issues': why,
                         'executed_at_patch_head': 'unknown', 'environment': 'unknown',
                         'producer_version': 'unknown'})
    checks = []
    for name, command in (report['commands'].items() if report else []):
        matches = [r for r in receipts if r['declaration'] == name and r['declared_command'] == command]
        latest = max(matches, key=lambda r: r['recorded_at']) if matches else None
        checks.append({'property': name, 'command': command,
                       'state': _check_state(latest) if latest else 'absent',
                       'receipt_key': latest['receipt_key'] if latest else None,
                       'association': latest['association'] if latest else 'unavailable'})
    value = {'schema_version': 1, 'kind': 'patchproof', 'patch': patch,
             'binding': {'state': 'bound' if bound else 'unavailable',
                         'meaning': 'current checkout and recorded input association, not universal patch safety',
                         'issues': list(dict.fromkeys(issues))},
             'verification': report, 'receipts': receipts, 'checks': checks,
             'coverage': {'unobserved_patch_paths': sorted(patch_paths - covered),
                          'unsupported_properties': ['API compatibility', 'database compatibility',
                                                     'security compatibility', 'behavioral compatibility']},
             'next_actions': ([] if bound else ['Resolve patch/report binding gaps before relying on input associations.'])
                             + (report['next_actions'] if report else ['Collect current execution receipts.'])
                             + ['Run the missing project-declared check: ' + c['command'] for c in checks if c['state'] == 'absent'],
             'limits': LIMITS, 'elapsed_seconds': round(time.monotonic() - started, 3)}
    return _portable(value, root)
