"""Associate an exact committed patch with scoped existing observations."""
import hashlib
import math
import os
import subprocess
from pathlib import Path
import time

from ..export import build as verification_report, markdown as verification_markdown, _portable, _text
from ..hosts.readiness import receipt_key
from ..ledger import Ledger
from ..parsers import DECLARED_KINDS
from .identity import collect
from .contract_report import inspect as contract_report
from .impact import inspect as impact_report, disabled as impact_disabled, qualify as qualify_impact
from ..impact import markdown as impact_markdown
from .execution_report import inspect as execution_report
from .policy import fingerprint as policy_fingerprint
from ..inputs.collection import capture as input_capture, markdown as input_markdown
from ..inputs.definition import raw as input_raw


LIMITS = [
    'Unsigned local evidence, not independent attestation or proof that a patch is safe.',
    'Binding means recorded inputs match the inspected checkout; legacy execution provenance is unknown unless separately qualified saved execution is present.',
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
                       ('.elevenpowers/config.json', 1024 * 1024),
                       ('.elevenpowers/contracts.json', 1024 * 1024),
                       ('.elevenpowers/patch-verification.json', 1024 * 1024),
                       ('.elevenpowers/input-roots.json', 65536),
                       ('elevenpowers.inputs.json', 65536),
                       ('elevenpowers.contracts.json', 65536)):
        if rel == '.elevenpowers/input-roots.json' and not (root/'elevenpowers.inputs.json').exists():
            continue  # Unconfigured users do not authorize reading unused approvals.
        if time.monotonic() >= deadline:
            raise TimeoutError('bundle deadline reached reading state')
        path = root / rel
        if rel in ('.elevenpowers/input-roots.json','elevenpowers.inputs.json'):
            raw = input_raw(path,limit,optional=True)
            values.append(hashlib.sha256(raw).hexdigest() if raw is not None else None)
            continue
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


def build(root, base='HEAD~1', head='HEAD', *, timeout=120, impact=False):
    """Read an unsigned bundle. Binding is not a task verdict or safety badge."""
    if not math.isfinite(timeout) or not 0 <= timeout <= 600:
        raise ValueError('bundle timeout must be between 0 and 600')
    started = time.monotonic()
    deadline = started + timeout
    root = Path(root).resolve(strict=True)
    external_inputs = input_capture(root,deadline)
    patch = collect(root, base, head, seconds=max(0, deadline - time.monotonic()))
    issues = list(patch['issues']) + list(patch['checkout']['issues'])
    report, records = None, {}
    contracts = {'schema': 1, 'complete': False, 'checks': [], 'issues': ['Contract inspection unavailable.'], 'evicted': 0, 'limits': []}
    impact_value = impact_disabled()
    fingerprints = []
    before = None
    policy_before = None
    redirects = ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR',
                 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES',
                 'GIT_CONFIG_COUNT', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG')
    if any(name in os.environ for name in redirects):
        issues.append('ambient Git repository/config overrides leave legacy report enumeration unqualified')
    try:
        if impact or external_inputs['state'] != 'not_configured':
            try:
                policy_before = policy_fingerprint(root, deadline)
            except (OSError, ValueError, TimeoutError, subprocess.SubprocessError):
                issues.append('repository ignore policy inspection unavailable or incomplete')
        before = _guard(root, deadline)
        ledger = Ledger.load(root)
        records = {receipt_key(record): record for record in ledger.evidence}
        report = verification_report(root, timeout=max(0, deadline - time.monotonic()))
        check = verification_report(root, timeout=max(0, deadline - time.monotonic()))
        fingerprints = [r['coverage']['source_fingerprint'] for r in (report, check)]
        contracts = contract_report(root, patch, deadline)
        after = _guard(root, deadline)
        if before != after:
            issues.append('ledger or project configuration changed during bundle collection')
        if _inputs(report) != _inputs(check):
            issues.append('observed inputs or receipts changed during bundle collection')
        if not report['coverage']['complete'] or not check['coverage']['complete']:
            issues.append('source, native edit or report coverage is incomplete')
    except (OSError, ValueError, TypeError, KeyError, AttributeError, TimeoutError) as exc:
        issues.append(type(exc).__name__ + ': evidence report unavailable or incomplete')
    if impact:
        impact_value = impact_report(root, patch, fingerprints, deadline)
        try:
            if policy_before is None or policy_before != policy_fingerprint(root, deadline):
                issues.append('repository ignore policy changed or unavailable during bundle collection')
            if before is None or before != _guard(root, deadline):
                issues.append('ledger or project configuration changed during impact collection')
        except (OSError, ValueError, TimeoutError, subprocess.SubprocessError) as exc:
            issues.append(type(exc).__name__ + ': final impact state guard unavailable')
    final = collect(root, base, head, seconds=max(0, deadline - time.monotonic()))
    if patch != final:
        issues.append('patch identity or checkout qualification changed during bundle collection')
    if not final['complete'] or not final['checkout']['eligible']:
        issues += final['issues'] + final['checkout']['issues']
    if time.monotonic() >= deadline:
        issues.append('bundle deadline reached; binding is incomplete')
    bound = patch['complete'] and patch['checkout']['eligible'] and report is not None and not issues
    qualify_impact(impact_value, bound)
    for contract in contracts['checks']:
        if not bound:
            contract['association'] = 'unavailable'
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
        kind = DECLARED_KINDS.get(name)
        matches = [r for r in receipts if kind is not None and r['kind'] == kind.value
                   and r['declaration'] == name and r['declared_command'] == command]
        # Match the portable exporter's later-entry tie rule, and never allow
        # individual tests to substitute for their aggregate command outcome.
        latest = max(reversed(matches), key=lambda r: r['recorded_at']) if matches else None
        checks.append({'property': name, 'command': command,
                       'state': _check_state(latest) if latest else 'absent',
                       'receipt_key': latest['receipt_key'] if latest else None,
                       'association': latest['association'] if latest else 'unavailable'})
    execution = execution_report(root, patch, receipts, deadline, bound, base=base, head=head)
    external_final = input_capture(root,deadline)
    if (external_inputs['state'] != external_final['state'] or
            external_inputs['fingerprint'] != external_final['fingerprint']):
        external_inputs = external_final
        external_inputs.update(state='incomplete',fingerprint=None)
        external_inputs['issues'].append('external inputs changed during bundle inspection')
    else:
        external_inputs = external_final
    if external_inputs['state'] == 'incomplete':
        for observation in execution['checks']:
            observation.update(association='unavailable',external_inputs_association='unavailable',
                               executed_at_patch_head='unknown')
            observation['association_issues'].append('final external input inspection is incomplete')
        if execution['state'] != 'absent':
            execution['state'] = 'incomplete'
    try:
        if external_inputs['state'] != 'not_configured':
            final_patch = collect(root,base,head,seconds=max(0,deadline-time.monotonic()))
            final_report = verification_report(root,timeout=max(0,deadline-time.monotonic()))
            if final_patch != patch or report is None or _inputs(final_report) != _inputs(report):
                issues.append('patch, checkout or source changed during external input inspection')
                bound = False
            if policy_before is None or policy_before != policy_fingerprint(root,deadline):
                issues.append('repository policy changed during external input inspection')
                bound = False
        if before is None or _guard(root, deadline) != before:
            issues.append('ledger or configuration changed during saved execution inspection')
            bound = False
    except (OSError, ValueError, TimeoutError) as error:
        issues.append(type(error).__name__ + ': final execution state guard unavailable')
        bound = False
    if not bound:
        covered.clear()
        qualify_impact(impact_value, False)
        for contract in contracts['checks']:
            contract['association'] = 'unavailable'
        for receipt in receipts:
            receipt['association'] = 'unavailable'
            if 'final bundle state inspection is unavailable' not in receipt['association_issues']:
                receipt['association_issues'].append('final bundle state inspection is unavailable')
        for check in checks:
            check['association'] = 'unavailable'
        for check in execution['checks']:
            check['association'] = 'unavailable'
            check['executed_at_patch_head'] = 'unknown'
            check['association_issues'].append('final bundle state inspection is unavailable')
        if execution['state'] != 'absent':
            execution['state'] = 'incomplete'
    value = {'schema_version': 1, 'kind': 'patchproof', 'patch': patch,
             'binding': {'state': 'bound' if bound else 'unavailable',
                         'meaning': 'current checkout and recorded input association, not universal patch safety',
                         'issues': list(dict.fromkeys(issues))},
             'verification': report, 'receipts': receipts, 'checks': checks, 'contracts': contracts,
             'impact': impact_value, 'execution': execution, 'external_inputs': external_inputs,
             'coverage': {'unobserved_patch_paths': sorted(patch_paths - covered),
                          'unsupported_properties': ['API compatibility', 'database compatibility',
                                                     'security compatibility', 'behavioral compatibility']},
             'next_actions': ([] if bound else ['Resolve patch/report binding gaps before relying on input associations.'])
                             + (report['next_actions'] if report else ['Collect current execution receipts.'])
                             + ['Run the missing project-declared check: ' + c['command'] for c in checks if c['state'] == 'absent'],
             'limits': LIMITS, 'elapsed_seconds': round(time.monotonic() - started, 3)}
    return _portable(value, root)


def markdown(value):
    patch, binding = value['patch'], value['binding']
    lines = ['# ElevenPowers PatchProof evidence bundle', '',
             '**Patch/input binding: ' + _text(binding['state']) + '**',
             'Binding associates observed inputs with this checkout; it does not certify safety.', '',
             '## Exact committed patch', '',
             'Base: ' + _text(patch['base'] or 'unavailable'),
             'Head: ' + _text(patch['head'] or 'unavailable'),
             'Patch identity: ' + _text(patch['patch_id'] or 'unavailable'),
             'Full tree-pair content digest: ' + _text(patch['content_digest'] or 'unavailable'),
             'Collection: ' + ('complete' if patch['complete'] else 'incomplete')
             + '; empty: ' + _text(patch['empty']), '',
             '| Change | Path | Previous path | Binary |', '|---|---|---|---|']
    for change in patch['changes']:
        lines.append('| ' + ' | '.join(_text(c) for c in (change['kind'], change['path'],
                     change['old_path'], change['binary'])) + ' |')
    if not patch['changes']:
        lines.append('| No collected changed paths | — | — | — |')
    lines += ['', '## Receipt associations', '',
              '| Command / identity | Result | Execution | Freshness | Patch association |',
              '|---|---|---|---|---|']
    for receipt in value['receipts']:
        lines.append('| ' + ' | '.join(_text(c) for c in (receipt['command'] or receipt['identity'],
                     receipt['result'], receipt['execution'], receipt['freshness'], receipt['association'])) + ' |')
    if not value['receipts']:
        lines.append('| No recorded receipts | — | — | — | unavailable |')
    lines += ['']
    for receipt in value['receipts']:
        lines += ['- ' + _text(receipt['identity']) + ': ' + _text(issue)
                  for issue in receipt['association_issues']]
    lines += ['', '## Project-declared checks', '']
    lines += ['- ' + _text(c['property']) + ': ' + _text(c['state']) + '; association '
              + _text(c['association']) + '; command ' + _text(c['command']) for c in value['checks']]
    if not value['checks']:
        lines.append('No project-declared checks are available; applicability is unknown.')
    execution = value['execution']
    lines += ['', '## Explicit execution observations', '',
              'Saved execution inspection: ' + _text(execution['state']), '',
              '| Properties | Outcome | Input association | Inspected execution head |',
              '|---|---|---|---|']
    for check in execution['checks']:
        lines.append('| ' + ' | '.join(_text(v) for v in (
            ', '.join(check['properties']), check['status'], check['association'],
            check['executed_at_patch_head'])) + ' |')
        lines += ['- ' + _text(issue) for issue in check['association_issues']]
    if not execution['checks']:
        lines.append('| No saved command associations | — | unavailable | unknown |')
    lines += ['', *['- ' + _text(issue) for issue in execution['issues'] + execution['limits']]]
    lines += ['', '## Declared contract checks', '',
              '| Contract / property | Result | Execution | Freshness | Patch association |',
              '|---|---|---|---|---|']
    for contract in value['contracts']['checks']:
        lines.append('| ' + ' | '.join(_text(c) for c in
            (contract['id'] + ' / ' + contract['property'], contract['result'], contract['execution'],
             contract['freshness'], contract['association'])) + ' |')
    if not value['contracts']['checks']:
        lines.append('| No declared contract observation | unknown | unobserved | unavailable | unavailable |')
    lines += ['', *['- ' + _text(issue) for issue in value['contracts']['issues']]]
    for contract in value['contracts']['checks']:
        lines += ['- ' + _text(contract['id']) + ': state ' + _text(contract['state'])
                  + '; path ' + _text(contract['path'])]
        if contract['producer']:
            lines += ['  Producer: ' + _text(contract['producer']) + '; inputs: '
                      + _text(contract['inputs']) + '; configuration: ' + _text(contract['configuration'])
                      + '; findings: ' + _text(contract['findings']) + '; limits: ' + _text(contract['limits'])]
        lines += ['- ' + _text(issue) for issue in contract['issues']]
    lines += ['- ' + _text(limit) for limit in value['contracts']['limits']]
    impact = value.get('impact', impact_disabled())
    lines += ['', '## ImpactGraph recommendations', '',
              'State: ' + _text(impact['state']) + '; patch association: ' + _text(impact['association']),
              'Recommendations are not execution evidence or proof of safety.', '']
    if impact['state'] == 'not_requested':
        lines += ['Use --impact for optional fresh graph scans.']
    else:
        for key in ('patch_id', 'content_digest', 'source_fingerprint', 'snapshot_digest',
                    'repository_policy_fingerprint', 'runtime_fingerprint', 'configuration', 'omitted_paths'):
            lines += [_text(key) + ': ' + _text(impact.get(key, 'unavailable'))]
        lines += ['- ' + _text(issue) for issue in impact['association_issues']]
        if impact['association'] != 'bound':
            lines += ['The following diagnostic recommendations are unqualified for this patch.']
        if impact['query'] is not None:
            lines += ['', impact_markdown(impact['query'])]
    lines += ['- ' + _text(limit) for limit in impact['limits']]
    lines += ['', input_markdown(value['external_inputs']), '', '## Coverage gaps and next actions', '']
    lines += ['- ' + _text(issue) for issue in binding['issues']]
    lines += ['- Unobserved patch path: ' + _text(p) for p in value['coverage']['unobserved_patch_paths']]
    lines += ['- Unsupported property; applicability unknown: ' + _text(p)
              for p in value['coverage']['unsupported_properties']]
    lines += ['- ' + _text(action) for action in value['next_actions']]
    lines += ['', '## Evidence limits', '', *['- ' + _text(limit) for limit in value['limits']]]
    if value['verification'] is not None:
        lines += ['', '## Existing verification report', '', verification_markdown(value['verification'])]
    return '\n'.join(lines) + '\n'
