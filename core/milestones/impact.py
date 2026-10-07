"""Explained graph leads are informational, never proof of unaffected behavior."""
import time

from ..impact import analyze, build as graph_build
from .definition import safe_path


def advise(root, milestones, changed, *, deadline):
    if not isinstance(changed, (list, tuple)) or any(not isinstance(p, str) for p in changed):
        raise ValueError('changed observations must be a list of relative paths')
    started = time.monotonic()
    result = {'state': 'incomplete', 'requested': list(changed[:256]),
              'omitted_observations': max(0, len(changed) - 256),
              'leads': [], 'issues': [], 'timings': {'graph_ms': 0.0, 'query_ms': 0.0},
              'safe_to_exclude': False,
              'limits': ['A missing graph path cannot establish that a milestone is unaffected.',
                         'These are dependency leads, not predicted failures or passing checks.',
                         'Graph and receipt snapshots have separate fingerprints and are not atomic.']}
    if len(changed) > 256:
        result['issues'].append('changed-path observation limit 256 reached')
        changed = changed[:256]
    for path in changed:
        safe_path(root, path)
    if not changed:
        result['issues'].append('no current changed-path observation is available for requested impact advice')
        return result
    seen = set()
    for milestone in milestones:
        for path in changed:
            if path in milestone['inputs']:
                key = milestone['id'], path
                if key not in seen:
                    result['leads'].append({'milestone': milestone['id'], 'input': path,
                                           'category': 'direct change observation', 'explanation': []})
                    seen.add(key)
            if len(result['leads']) >= 256:
                result['issues'].append('milestone impact result or time budget reached')
                return result
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        result['issues'].append('milestone deadline reached before impact advice')
        return result
    graph_started = time.monotonic()
    graph = graph_build(root, seconds=min(remaining, 120))
    result['timings']['graph_ms'] = round((time.monotonic() - graph_started) * 1000, 3)
    query_started = time.monotonic()
    query = analyze(graph, list(dict.fromkeys(changed)))
    result['timings']['query_ms'] = round((time.monotonic() - query_started) * 1000, 3)
    result['graph_fingerprint'] = query['source_fingerprint']
    result['coverage'] = query['coverage']
    result['issues'] += query['coverage']['issues']
    for milestone in milestones:
        for candidate in [*query['affected'], *query['tests']]:
            key = milestone['id'], candidate['path']
            if candidate['path'] in milestone['inputs'] and key not in seen:
                result['leads'].append({'milestone': milestone['id'], 'input': candidate['path'],
                                       'category': candidate['category'], 'explanation': candidate['explanation']})
                seen.add(key)
            if len(result['leads']) >= 256 or time.monotonic() >= deadline:
                result['issues'].append('milestone impact result or time budget reached')
                result['leads'] = result['leads'][:256]
                return result
    result['state'] = 'incomplete' if result['issues'] else 'available'
    return result
