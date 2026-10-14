"""Read-only exact-patch command plans; impact leads never remove checks."""
import math
from pathlib import Path
import time

from ..config import load
from ..export import _text
from ..parsers import DECLARED_KINDS
from .report import build, _guard
from .execution_state import digest


MAX_DECLARATIONS = 64


def budgets(seconds, command_seconds):
    if not math.isfinite(seconds) or not 0 <= seconds <= 600:
        raise ValueError('verification seconds must be between 0 and 600')
    if not math.isfinite(command_seconds) or not 0 < command_seconds <= 300:
        raise ValueError('command seconds must be greater than 0 and at most 300')
    return {'seconds': seconds, 'command_seconds': command_seconds,
            'output_bytes_per_command': 8 * 1024 * 1024,
            'cleanup_seconds_per_command': 5,
            'max_declarations': MAX_DECLARATIONS}


def plan(root, base='HEAD~1', head='HEAD', *, seconds=120, command_seconds=30, impact=False, reuse=True):
    limits = budgets(seconds, command_seconds)
    root = Path(root).resolve(strict=True)
    deadline = time.monotonic() + seconds
    try:
        before = _guard(root, deadline)
    except (OSError, ValueError, TimeoutError):
        before = None
    config = load(root)
    bundle = build(root, base, head, timeout=max(0, deadline - time.monotonic()), impact=impact)
    issues = list(bundle['binding']['issues'])
    issues.extend(bundle['execution']['issues'])
    from ..inputs.scopes import project
    for command in config.commands.values():
        required=project(bundle['external_inputs'],command,declared=True)
        if required['state']=='incomplete':
            issues.extend(required['issues'] or ['required external command scope is incomplete'])
    try:
        if before is None or _guard(root, deadline) != before or config != load(root):
            issues.append('command configuration or evidence state changed/unavailable during planning')
    except (OSError, ValueError, TimeoutError):
        issues.append('command configuration or evidence state inspection unavailable')
    if not config.verifies:
        issues.append('off profile is passive; explicit verification is unavailable')
    declared = bundle['checks']
    omitted = max(0, len(declared) - MAX_DECLARATIONS)
    if omitted:
        issues.append('declaration limit 64 reached; execution plan is incomplete')
    groups = {}
    for check in declared[:MAX_DECLARATIONS]:
        command = check['command']
        raw = config.commands.get(check['property'], '')
        supported = check['property'] in DECLARED_KINDS and len(raw) <= 8192 and '\0' not in raw
        # Unsupported properties cannot silently become verified by a supported alias.
        key = (digest(raw), supported)
        item = groups.setdefault(key, {'command': command, 'properties': [],
            'required': True, 'supported': supported, 'state': check['state'],
            'action': 'run', 'reasons': [], 'receipt_keys': []})
        item['properties'].append(check['property'])
        item['reasons'].append(check['property'] + ': ' + check['state'])
        if check['receipt_key']:
            item['receipt_keys'].append(check['receipt_key'])
        if check['state'] != 'current':
            item['state'] = check['state']
        if not supported:
            item['action'] = 'unsupported'
            issues.append('unsupported declaration or command: ' + check['property'])
    if not declared:
        issues.append('no project-declared checks; verification applicability is unknown')
    executions = bundle['execution']['checks']
    for item in groups.values():
        raw = config.commands.get(item['properties'][0], '')
        item['command_digest'] = digest(raw)
        observed = next((e for e in executions if e['command_digest'] == item['command_digest']), None)
        if (reuse and item['supported'] and item['state'] == 'current' and observed
                and observed['status'] == 'passed' and observed['association'] == 'bound'
                and set(item['receipt_keys']) == set(observed['receipt_keys'])):
            item['action'] = 'reuse'
    return {'schema_version': 1, 'kind': 'patchproof_plan',
            'ready': bundle['binding']['state'] == 'bound' and not issues,
            'patch_id': bundle['patch']['patch_id'], 'head': bundle['patch']['head'],
            'checks': list(groups.values()), 'budgets': limits, 'estimated_seconds': None,
            'omitted_declarations': omitted, 'issues': list(dict.fromkeys(issues)),
            'bundle': bundle, 'limits': [
                'All supported declared commands remain required; impact is advisory.',
                'Current legacy receipts do not establish exact execution provenance or reuse eligibility.',
                'Cost is unknown; budgets are limits, not duration estimates.',
                'Planning executes no project checks and writes no project state.']}


def markdown(value):
    lines = ['# ElevenPowers PatchProof verification plan', '',
             'Ready for explicit execution: ' + _text(value['ready']),
             'Patch identity: ' + _text(value['patch_id']), '',
             '| Properties | Required | Evidence | Action | Declared command |',
             '|---|---|---|---|---|']
    for check in value['checks']:
        lines.append('| ' + ' | '.join(_text(v) for v in (
            ', '.join(check['properties']), check['required'], check['state'],
            check['action'], check['command'])) + ' |')
    lines += ['', 'Shared seconds: ' + _text(value['budgets']['seconds']),
              'Per-command seconds: ' + _text(value['budgets']['command_seconds']),
              'Estimated duration: unknown; cleanup has a separate allowance.', '']
    lines += ['- ' + _text(issue) for issue in value['issues'] + value['limits']]
    if value['bundle']['impact']['state'] != 'not_requested':
        from ..impact import markdown as impact_markdown
        impact = value['bundle']['impact']
        lines += ['', '## Advisory impact', '',
                  'Input association: ' + _text(impact['association'])]
        if impact.get('query'):
            lines += ['', impact_markdown(impact['query'])]
    return '\n'.join(lines) + '\n'
