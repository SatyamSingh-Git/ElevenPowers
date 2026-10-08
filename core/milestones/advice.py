"""Strict optional delivery policy and bounded informational context."""
from ..redact import scrub

DEFAULTS = {'enabled': False, 'seconds': 1.0, 'cooldown': 30, 'max_attempts': 3}


def policy(raw):
    if not isinstance(raw, dict) or set(raw) - set(DEFAULTS):
        raise ValueError('milestone_advice must contain only supported fields')
    value = {**DEFAULTS, **raw}
    if type(value['enabled']) is not bool:
        raise ValueError('milestone_advice.enabled must be boolean')
    for name, low, high in [('seconds', .1, 5), ('cooldown', 0, 3600), ('max_attempts', 1, 10)]:
        item = value[name]
        # Comparison before conversion also rejects huge integers without overflow.
        if type(item) not in (int, float) or not low <= item <= high:
            raise ValueError('invalid milestone_advice.' + name)
    if type(value['max_attempts']) is not int:
        raise ValueError('milestone_advice.max_attempts must be an integer')
    return value if value['enabled'] else None


def _preview(value, limit=350):
    text = ' '.join(scrub(str(value)).split())
    return text if len(text) <= limit else text[:limit] + ' [truncated preview]'


def render_with_checks(report):
    """Return bounded text and only exact command lines retained in that text."""
    coverage = report['coverage']
    lines = ['ElevenPowers milestone advice (informational, not proof).',
             'Keep fallback verification; missing paths never establish unaffected behavior.',
             'Evidence: ' + _preview(report['state']) +
             ('; INCOMPLETE coverage.' if not coverage['complete'] else '; declared scope only.')]
    commands = report['rechecks'].get('commands', [])
    visible = []
    for command in commands[:6]:
        states = ', '.join(_preview(m['id'], 40) + ': ' + _preview(m['state'], 20)
                           for m in command['milestones'][:8])
        if len(command['milestones']) > 8:
            states += f"; {len(command['milestones']) - 8} milestone states omitted"
        lines.append(f"- {_preview(command['priority'], 20)} / {_preview(command['kind'], 30)}: "
                     f"{_preview(command['command'])} [{states}]")
        if _preview(command['command']) == command['command']:
            visible.append((command, len('\n'.join(lines))))
        reasons = command.get('reasons', [])
        for reason in reasons[:3]:
            lines.append('  ' + _preview(f"{reason['milestone']}: {reason['input']} ({reason['category']})", 180))
        omitted = max(0, len(reasons) - 3) + command.get('omitted_reasons', 0)
        if omitted:
            lines.append(f'  {omitted} reasons omitted; inspect the full milestone report.')
    if len(commands) > 6:
        lines.append(f'{len(commands) - 6} commands omitted; retain their fallback verification.')
    for issue in coverage.get('issues', [])[:3]:
        lines.append('Gap: ' + _preview(issue, 180))
    if len(coverage.get('issues', [])) > 3:
        lines.append(f"{len(coverage['issues']) - 3} additional coverage issues omitted.")
    lines.append('Full view: ep_milestones.py --project PATH --impact. Advice executes no checks.')
    text = '\n'.join(lines)
    retained = len(text) if len(text) <= 6000 else 5900
    context = text if len(text) <= 6000 else text[:5900] + '\nContext truncated; consult the full report and keep all fallback checks.'
    return context, [command for command, end in visible if end <= retained]


def render(report):
    return render_with_checks(report)[0]
