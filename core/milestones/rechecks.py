"""Rank declared commands by explained leads, never discard fallback checks."""
import time

PRIORITIES = ('direct', 'dependency', 'fallback')


def plan(milestones, advice, *, complete):
    """Consume validated report rows; evidence states remain authoritative."""
    started = time.monotonic()
    issues = list(advice.get('issues', []))
    if not complete:
        issues.append('Resolve incomplete report coverage before relying on recommendations.')
    leads = {}
    for item in advice.get('leads', []):
        leads.setdefault(item['milestone'], []).append(item)
    commands = {}
    for milestone in milestones:
        for check in milestone['checks']:
            key = check['kind'], check['command']
            value = commands.setdefault(key, {
                'kind': key[0], 'command': key[1], 'origin': 'project declaration',
                'priority': 'fallback', 'needs_refresh': False, 'milestones': [],
                'reasons': [], 'omitted_reasons': 0, 'qualifications': [], 'issues': []})
            value['milestones'].append({'id': milestone['id'], 'state': check['state']})
            value['needs_refresh'] |= check['state'] != 'CURRENT'
            for field in ('issues', 'qualifications'):
                for message in check.get(field, []):
                    if message not in value[field]:
                        value[field].append(message)
            for reason in leads.get(milestone['id'], []):
                priority = 'direct' if reason['category'] == 'direct change observation' else 'dependency'
                if PRIORITIES.index(priority) < PRIORITIES.index(value['priority']):
                    value['priority'] = priority
                if len(value['reasons']) < 16:
                    value['reasons'].append(reason)
                else:
                    value['omitted_reasons'] += 1
    for value in commands.values():
        if value['omitted_reasons']:
            issues.append('command explanation limit 16 reached; additional leads omitted')
        if value['priority'] == 'fallback':
            value['qualifications'].append('No available impact witness; dependency relevance is unknown. Keep fallback verification.')
    issues = list(dict.fromkeys(issues))
    return {'schema': 1, 'state': 'incomplete' if issues or advice['state'] != 'available' else 'available',
            'commands': sorted(commands.values(), key=lambda c: (
                not c['needs_refresh'], PRIORITIES.index(c['priority']), c['kind'], c['command'])),
            'safe_to_exclude': False, 'issues': issues,
            'policy': 'Refresh-needed checks first, then direct, dependency and fallback. '
                      'Priority is a relationship lead, not a failure probability or permission to skip checks.',
            'timings': {'ranking_ms': round((time.monotonic() - started) * 1000, 3)}}
