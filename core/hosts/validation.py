"""Portable dated captures of the existing native exercise inspector."""
from datetime import datetime, timezone
import math
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
