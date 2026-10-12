"""Fresh read-only PatchProof collection for an informational GitHub export."""
import hashlib
import json
from pathlib import Path

from ..redact import scrub_values
from . import report
from .github_context import declared


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def build(root, base='HEAD~1', head='HEAD', *, repository, event=None, timeout=120, impact=False):
    before = declared(repository, event)
    bundle = report.build(Path(root), base, head, timeout=timeout, impact=impact)
    if declared(repository, event) != before:
        raise ValueError('event subject changed during collection')
    patch = bundle['patch']
    subject = {**before, 'base': patch['base'], 'head': patch['head'],
               'patch_id': patch['patch_id'], 'content_digest': patch['content_digest']}
    if not patch['base'] or not patch['head'] or not patch['patch_id']:
        subject['state'] = 'unavailable'
        subject['issues'].append('selected patch identity is unavailable')
    elif before['pull_request'] is not None:
        if patch['base'] != before['expected_base'] or patch['head'] != before['expected_head']:
            raise ValueError('selected patch does not match PR base and head')
        subject['state'] = 'matched_event'
    else:
        subject['state'] = 'declared'
    public = scrub_values(bundle)
    return {'schema_version': 1, 'kind': 'patchproof_github', 'subject': subject,
            'meaning': 'informational evidence export, not patch safety',
            'bundle_sha256': hashlib.sha256(canonical(public)).hexdigest(), 'bundle': public,
            'limits': [
                'Repository and event metadata are declared, not independently authenticated.',
                'Evidence freshness describes collection time; later edits require a new export.',
                'Successful presentation or upload is not a correctness gate or independent attestation.',
                'The original bundle retains all evidence outcomes, scopes and qualifications.',
            ]}
