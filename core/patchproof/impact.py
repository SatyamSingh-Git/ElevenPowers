"""Compose fresh graph leads with an exact patch; never promote leads to receipts."""
import hashlib
import json
import subprocess
import time

from ..hosts.provenance import fingerprint as runtime_fingerprint
from ..impact import analyze, build as graph_build
from .policy import fingerprint as policy_fingerprint, PolicyError


CONFIGURATION = {'adapter': 'patchproof-impact/1', 'seconds_per_scan': 30,
                 'max_paths': 256, 'max_depth': 6, 'max_results': 100,
                 'compiler': False, 'observations': False, 'history': 0}
LIMITS = [
    'Impact is a recommendation, not execution evidence, predicted failure or proof of safety.',
    'Missing paths never justify skipping declared checks, fallback candidates or full verification.',
    'Only current default adapters and project declarations are used; no external graph is accepted.',
    'The graph describes the current head; removed or previous rename paths may be unavailable.',
    'Before/after snapshots are bounded, not atomic; intervening reverted changes are undetectable.',
]


def disabled():
    return {'schema': 1, 'state': 'not_requested', 'association': 'unavailable',
            'association_issues': [], 'query': None, 'limits': LIMITS}


def _snapshot(graph):
    return hashlib.sha256(json.dumps(graph.to_dict(), sort_keys=True,
                         separators=(',', ':')).encode()).hexdigest()


def inspect(root, patch, fingerprints, deadline):
    """Scan only this root twice; fingerprints come from both verification reads."""
    paths = sorted({p for c in patch['changes'] for p in (c['path'], c['old_path'])})
    value = {'schema': 1, 'state': 'incomplete', 'association': 'unavailable',
             'patch_id': patch['patch_id'], 'content_digest': patch['content_digest'],
             'configuration': dict(CONFIGURATION), 'runtime_fingerprint': '',
             'source_fingerprint': '', 'snapshot_digest': '', 'repository_policy_fingerprint': '',
             'omitted_paths': max(0, len(paths) - CONFIGURATION['max_paths']),
             'association_issues': [], 'query': None, 'limits': LIMITS}
    why = value['association_issues']
    if not patch['complete'] or not patch['checkout']['eligible']:
        why.append('exact patch/current checkout association is unavailable')
    if value['omitted_paths']:
        why.append('impact path limit 256 reached; requested patch scope is incomplete')
    try:
        if time.monotonic() >= deadline:
            raise TimeoutError('impact bundle deadline reached')
        value['runtime_fingerprint'] = runtime_fingerprint()
        value['repository_policy_fingerprint'] = policy_fingerprint(root, deadline)
        graph = graph_build(root, seconds=min(30, max(0, deadline - time.monotonic())))
        value['source_fingerprint'] = graph.fingerprint
        value['snapshot_digest'] = _snapshot(graph)
        if paths:
            value['query'] = analyze(graph, paths[:256], max_depth=6, max_results=100)
        after = graph_build(root, seconds=min(30, max(0, deadline - time.monotonic())))
        if value['repository_policy_fingerprint'] != policy_fingerprint(root, deadline):
            why.append('repository ignore policy changed during impact collection')
        if value['snapshot_digest'] != _snapshot(after):
            why.append('graph inputs, declarations, scan policy or relationships changed during collection')
        if value['runtime_fingerprint'] != runtime_fingerprint():
            why.append('runtime producer changed during impact collection')
        for snapshot in (graph, after):
            if not snapshot.coverage.get('inputs_complete') or not snapshot.coverage.get('declarations_complete'):
                why.append('graph input or declaration coverage is incomplete')
            if (len(fingerprints) != 2 or not all(fingerprints)
                    or any(f != snapshot.coverage.get('evidence_source_fingerprint') for f in fingerprints)):
                why.append('graph/evidence source fingerprints are incompatible')
        if time.monotonic() >= deadline:
            why.append('impact bundle deadline reached; collection is incomplete')
        query_complete = value['query'] is None or value['query']['coverage']['complete']
        value['state'] = 'incomplete' if why or not query_complete else ('available' if paths else 'empty')
    except PolicyError as exc:
        why.append(str(exc))
    except (OSError, ValueError, TypeError, KeyError, RecursionError, TimeoutError, subprocess.SubprocessError) as exc:
        why.append(type(exc).__name__ + ': impact collection unavailable or incomplete')
    value['association_issues'] = list(dict.fromkeys(why))
    value['association'] = 'unavailable' if why else 'bound'
    return value


def qualify(value, eligible):
    """Final bundle qualification remains separate from semantic graph coverage."""
    if value['state'] != 'not_requested' and not eligible:
        value['association'] = 'unavailable'
        value['association_issues'].append('final patch/report binding is unavailable')
