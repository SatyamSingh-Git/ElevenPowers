"""Bounded GFM and no-overwrite publication of a freshly built presentation."""
from collections import Counter
import hashlib
from pathlib import Path
import tempfile
import unicodedata

from ..export import _text, write
from ..redact import scrub, scrub_values
from .github import canonical

MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_SUMMARY_BYTES = 64 * 1024
MAX_ROWS = 64
MAX_TEXT = 384


def _cell(value):
    value = scrub(str(value))
    suffix = ''
    if len(value) > MAX_TEXT:
        value, suffix = value[:MAX_TEXT], ' (truncated; full value in artifact)'
    value = ''.join(f'\\u{ord(c):04x}' if unicodedata.category(c) in {'Cc', 'Cf'}
                    and c not in '\n\r\t' else c for c in value)
    return _text(value + suffix).replace('@', '&#64;')


def _validate(value):
    if (not isinstance(value, dict) or type(value.get('schema_version')) is not int
            or value['schema_version'] != 1 or value.get('kind') != 'patchproof_github'):
        raise ValueError('unsupported presentation schema')
    public = scrub_values(value)
    if public.get('bundle_sha256') != hashlib.sha256(canonical(public['bundle'])).hexdigest():
        raise ValueError('presentation bundle hash does not match')
    subject, patch = public['subject'], public['bundle']['patch']
    if any(subject[key] != patch[key] for key in ('base', 'head', 'patch_id', 'content_digest')):
        raise ValueError('presentation subject does not match bundle')
    return public


def _table(lines, title, headings, rows):
    lines += ['', '## '+title, '', '| '+ ' | '.join(headings)+' |',
              '|'+ '|'.join('---' for _ in headings)+'|']
    for row in rows[:MAX_ROWS]:
        lines.append('| '+' | '.join(_cell(c) for c in row)+' |')
    if not rows:
        lines.append('| No observations |' + ' — |' * (len(headings)-1))
    if len(rows) > MAX_ROWS:
        lines += ['', f'{len(rows)-MAX_ROWS} rows omitted from summary; full records are in evidence.json.']


def _list(lines, title, values):
    lines += ['', '## '+title, '']
    lines += ['- '+_cell(v) for v in values[:MAX_ROWS]] or ['No observations recorded.']
    if len(values) > MAX_ROWS:
        lines += [f'{len(values)-MAX_ROWS} rows omitted from summary; full records are in evidence.json.']


def markdown(value):
    value = _validate(value)
    subject, bundle = value['subject'], value['bundle']
    verification = bundle.get('verification') or {}
    lines = ['# ElevenPowers GitHub evidence', '',
             '**Informational evidence export, not patch safety.**',
             'A successful export/upload means presentation completed; it does not certify the code.', '',
             'Repository (declared): '+_cell(subject['repository']),
             'Head repository: '+_cell(subject['head_repository'] or 'unavailable'),
             'Subject: '+_cell(subject['state'])+'; PR: '+_cell(subject['pull_request'] or 'not supplied'),
             'Base: '+_cell(subject['base'] or 'unavailable'),
             'Head: '+_cell(subject['head'] or 'unavailable'),
             'Patch identity: '+_cell(subject['patch_id'] or 'unavailable'),
             'Full tree-pair digest: '+_cell(subject['content_digest'] or 'unavailable'),
             'Public bundle SHA-256: '+_cell(value['bundle_sha256']), '',
             'Patch/input binding at inspection: **'+_cell(bundle['binding']['state'])+'**',
             'Task state as reported: **'+_cell(verification.get('state', 'unavailable'))+'**',
             'Freshness and association describe this collection, not future edits.']
    counts = Counter(c['state'] for c in bundle['checks'])
    lines += ['', 'Reported declared-check states: '+(', '.join(
        _cell(k)+': '+str(v) for k, v in sorted(counts.items())) or 'no declarations; applicability unknown')]
    lines += ['Unobserved patch paths: '+str(len(bundle['coverage']['unobserved_patch_paths']))
              +'; unsupported properties: '+str(len(bundle['coverage']['unsupported_properties'])),
              'Report coverage complete: '+_cell(verification.get('coverage', {}).get('complete', 'unavailable'))]
    header = list(lines)
    external = bundle.get('external_inputs',{'state':'not_configured','fingerprint':None,'witnesses':[],'issues':[]})
    lines += ['Declared external inputs: '+_cell(external['state'])+'; witnesses: '+str(len(external['witnesses'])),
              'Selected-input fingerprint: '+_cell(external['fingerprint'] or 'unavailable'),
              'Source-only receipts do not establish external freshness or the complete environment.']
    header = list(lines)
    _table(lines,'Declared external inputs',['Witness','Root label','Collection','Files'],
           [(w['id'],w['root'],w['state'],w['files']) for w in external['witnesses']])
    _list(lines,'External input gaps',external['issues'])
    _table(lines, 'Project-declared checks', ['Property', 'Reported state', 'Association', 'Command'],
           [(c['property'], c['state'], c['association'], c['command']) for c in bundle['checks']])
    _table(lines, 'Receipt observations', ['Command', 'Result', 'Execution', 'Freshness', 'Association'],
           [(r['command'] or r['identity'], r['result'], r['execution'], r['freshness'], r['association'])
            for r in bundle['receipts']])
    execution = bundle.get('execution', {})
    _table(lines, 'Saved exact-patch execution', ['Properties', 'Status', 'Association'],
           [(', '.join(c['properties']), c['status'], c['association']) for c in execution.get('checks', [])])
    contracts = bundle.get('contracts', {})
    _table(lines, 'Declared contract observations', ['Contract', 'State', 'Result', 'Association'],
           [(c['id'], c['state'], c['result'], c['association']) for c in contracts.get('checks', [])])
    impact = bundle.get('impact', {})
    lines += ['', '## Optional impact advice', '',
              'State: '+_cell(impact.get('state', 'unavailable'))+'; association: '+_cell(impact.get('association', 'unavailable'))+'.',
              'Explained paths and candidates remain advice; they never justify skipping a required check. Full graph details are in the artifact.']
    _list(lines, 'Unobserved patch paths', bundle['coverage']['unobserved_patch_paths'])
    _list(lines, 'Unsupported properties', bundle['coverage']['unsupported_properties'])
    _list(lines, 'Qualifications', subject['issues']+bundle['binding']['issues']
          +verification.get('coverage', {}).get('issues', [])+execution.get('issues', [])
          +contracts.get('issues', [])+impact.get('issues', []))
    _list(lines, 'Next actions', bundle['next_actions'])
    _list(lines, 'Trust and limits', value['limits']+bundle['limits'])
    text = '\n'.join(lines)+'\n'
    if len(text.encode('utf-8')) > MAX_SUMMARY_BYTES:
        # Keep identities and full state counts when rich tables exceed the cap.
        groups = [('Declared checks', bundle['checks']), ('Receipts', bundle['receipts']),
                  ('Saved executions', execution.get('checks', [])),
                  ('Contracts', contracts.get('checks', []))]
        groups.append(('External input witnesses',external['witnesses']))
        omissions = [f'{name}: {len(rows)} rows omitted by the byte fallback; '
                     f'{max(0, len(rows)-MAX_ROWS)} rows omitted by the row cap.'
                     for name, rows in groups if rows]
        text = '\n'.join(header)+('\n\nDetailed rows omitted because the summary byte limit was reached. '
               'Cells over 384 characters are truncated in bounded rendering. '
               'All evidence, missing/failed/stale/incomplete states and qualifications remain in evidence.json.\n')
        text += '\n'.join(omissions)+'\n'
    if len(text.encode('utf-8')) > MAX_SUMMARY_BYTES:
        raise ValueError('summary byte limit exceeded')
    return text


def publish(value, destination=None, *, project):
    public = _validate(value)
    data = canonical(public)+b'\n'
    if len(data) > MAX_ARTIFACT_BYTES:
        raise ValueError('artifact byte limit exceeded')
    summary = markdown(public)
    project = Path(project).resolve(strict=True)
    if destination is None:
        parent = Path(tempfile.gettempdir()).resolve(strict=True)
        if parent == project or parent.is_relative_to(project):
            raise ValueError('publication must be outside the inspected project')
        destination = Path(tempfile.mkdtemp(prefix='ep-patchproof-', dir=parent))
    else:
        destination = Path(destination).absolute()
        if destination.resolve() != destination or destination.is_symlink():
            raise ValueError('linked publication path is unavailable')
        if destination == project or destination.is_relative_to(project):
            raise ValueError('publication must be outside the inspected project')
        destination.mkdir()  # Atomic refusal of an existing directory.
    paths = {'directory': destination, 'evidence': destination/'evidence.json',
             'summary': destination/'summary.md',
             'artifact_name': 'patchproof-'+(public['subject']['patch_id'] or 'unavailable')[:16]
                              +'-'+public['bundle_sha256'][:16]}
    write(paths['evidence'], data.decode('utf-8'))
    write(paths['summary'], summary)
    return paths
