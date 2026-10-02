"""Portable dated captures of the existing native exercise inspector."""
from datetime import datetime, timezone
import math
import re
import time

from . import acceptance, probes
from .provenance import fingerprint
from .setup import PATHS

LANGUAGES = ('python', 'javascript')
CHECKS = ('test_unchanged', 'runtime_identity', 'project_configuration',
          'native_configuration', 'source_changed', 'host_version', 'generation',
          'command', 'startup_runtime', 'startup_after_preparation',
          'completion_after_commands', 'fresh_pipeline')
LIMITS = ['Unsigned local exercise observations, not host authentication or production patch certification.',
          'Saved captures describe their creation time; rerun after runtime or installed-version changes.']


def capture(host, root, timeout=10, observe_version=False):
    if host not in PATHS:
        raise ValueError('unsupported host')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 120:
        raise ValueError('capture seconds must be within 0–120')
    started = time.monotonic()
    before = fingerprint()
    version = probes.probe(host, min(5, timeout)) if observe_version else {
        'state': 'not_requested', 'version': '', 'source': 'unavailable'}
    result = acceptance.inspect(host, root, max(0, timeout - (time.monotonic() - started)))
    state = result['state']
    if (fingerprint() != before or result.get('runtime_fingerprint') != before or
            time.monotonic() - started >= timeout or
            (observe_version and (version['state'] != 'observed' or version['version'] != result.get('host_version')))):
        state = 'incomplete'
    if state == 'passed' and version['state'] != 'observed':
        state = 'waiting'
    return {'schema_version': 1, 'kind': 'native_acceptance', 'host': host,
            'language': result.get('language', 'unknown'), 'state': state,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'runtime_fingerprint': before, 'version': version,
            'checks': {name: result.get('checks', {}).get(name) is True for name in CHECKS},
            'outcomes': {name: result.get('outcomes', {}).get(name) is True for name in ('pass', 'fail', 'incomplete')},
            'limits': LIMITS.copy()}


def _validate(record):
    fields = {'schema_version', 'kind', 'host', 'language', 'state', 'generated_at',
              'runtime_fingerprint', 'version', 'checks', 'outcomes', 'limits'}
    try:
        if not isinstance(record, dict) or set(record) != fields:
            raise ValueError('unknown or missing capture fields')
        if (type(record['schema_version']) is not int or record['schema_version'] != 1 or
                record['kind'] != 'native_acceptance' or record['host'] not in PATHS or
                record['language'] not in LANGUAGES or
                record['state'] not in ('passed', 'failed', 'waiting', 'incomplete') or
                not re.fullmatch('[a-f0-9]{64}', record['runtime_fingerprint'])):
            raise ValueError('invalid capture identity')
        date = datetime.fromisoformat(record['generated_at'])
        if date.tzinfo is None or date > datetime.now(timezone.utc):
            raise ValueError('invalid capture time')
        for name, keys in (('checks', CHECKS), ('outcomes', ('pass', 'fail', 'incomplete'))):
            if set(record[name]) != set(keys) or any(type(v) is not bool for v in record[name].values()):
                raise ValueError('invalid capture check')
        version = record['version']
        if (set(version) != {'state', 'version', 'source'} or
                version['state'] not in ('observed', 'missing', 'incomplete', 'not_requested') or
                version['source'] not in ('installed_probe', 'unavailable') or
                not isinstance(version['version'], str) or len(version['version']) > 80 or
                (version['version'] and not re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][\w.-]+)?', version['version']))):
            raise ValueError('invalid capture version')
    except (TypeError, KeyError, AttributeError) as exc:
        raise ValueError('malformed capture') from exc


def matrix(records):
    if not isinstance(records, list) or len(records) > 100:
        raise ValueError('matrix accepts at most 100 captures')
    runtime = fingerprint()
    grouped = {}
    for record in records:
        _validate(record)
        grouped.setdefault((record['host'], record['language']), []).append(record)
    cells = []
    for host in PATHS:
        for language in LANGUAGES:
            entries = grouped.get((host, language), [])
            cell = {'host': host, 'language': language, 'state': 'waiting', 'version': '', 'observed_at': '',
                    'reason': 'No saved native capture supplied.'}
            if len(entries) > 1:
                cell.update(state='incomplete', reason='Duplicate captures require an explicit single choice.')
            elif entries:
                record = entries[0]
                state = record['state']
                qualified = (record['runtime_fingerprint'] == runtime and
                             record['version']['state'] == 'observed' and
                             record['version']['source'] == 'installed_probe' and bool(record['version']['version']) and
                             all(record['checks'].values()) and all(record['outcomes'].values()))
                if record['runtime_fingerprint'] != runtime or (state == 'passed' and not qualified):
                    state = 'incomplete'
                cell.update(state=state, version=record['version']['version'], observed_at=record['generated_at'],
                            reason='Dated saved observation; not a fresh installed-host certification.')
            cells.append(cell)
    if fingerprint() != runtime:
        for cell in cells:
            cell.update(state='incomplete', reason='Runtime changed during aggregation.')
    return {'schema_version': 1, 'kind': 'native_matrix', 'runtime_fingerprint': runtime,
            'generated_at': datetime.now(timezone.utc).isoformat(), 'cells': cells,
            'passed': sum(c['state'] == 'passed' for c in cells), 'total': len(cells), 'limits': LIMITS.copy()}


def render(value):
    lines = ['# ElevenPowers native validation', '', f"Runtime: `{value['runtime_fingerprint']}`", '']
    if value['kind'] == 'native_matrix':
        lines += [f"Dated native exercise cells passed: {value['passed']}/{value['total']}", '',
                  '| Host | Language | State | Version | Observed at |', '|---|---|---|---|---|']
        lines += [f"| {c['host']} | {c['language']} | {c['state']} | {c['version']} | {c['observed_at']} |" for c in value['cells']]
    else:
        lines += [f"{value['host']} / {value['language']}: **{value['state']}**", '',
                  f"Version: {value['version']['version'] or value['version']['state']}", '',
                  *[f'- {key}: {present}' for key, present in {**value['checks'], **value['outcomes']}.items()]]
    return '\n'.join([*lines, '', *['Limit: ' + limit for limit in value['limits']], ''])
