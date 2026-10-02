"""Bounded read-only health sampling; every attempted read remains visible."""
from datetime import datetime, timezone
import math
from pathlib import Path
import platform
import re
import sys
import time

from .. import health
from .provenance import fingerprint
from .setup import PATHS


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def measure(host, root, repeats=3, timeout=60):
    if host not in PATHS or type(repeats) is not int or not 1 <= repeats <= 20:
        raise ValueError('known host and 1–20 repeats required')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 120:
        raise ValueError('sampling seconds must be within 0–120')
    root = Path(root).resolve(strict=True)
    started = time.monotonic()
    deadline = started + timeout
    runtime = fingerprint()
    samples = []
    retained = {}
    command_times = {'samples': 0, 'median_ms': None, 'p95_ms': None}
    for _ in range(repeats):
        begin = time.monotonic()
        if begin >= deadline:
            break
        sample = {'state': 'failed', 'elapsed_ms': 0., 'health_state': 'unavailable',
                  'task_state': 'unavailable', 'coverage': {'complete': False, 'files': 0, 'bytes': 0},
                  'source_fingerprint': '', 'timings': {}}
        try:
            value = health.inspect(host, root, timeout=max(0, deadline - begin))
            sample.update(state='complete' if value['coverage']['complete'] else 'incomplete',
                          health_state=value['health']['state'], task_state=value['task_state'],
                          coverage={k: value['coverage'][k] for k in ('complete', 'files', 'bytes')},
                          source_fingerprint=value.get('report_coverage', {}).get('source_fingerprint', ''),
                          timings={k: value['timings'].get(k) for k in ('health_read_ms', 'source_snapshot_ms', 'report_ms')})
            if (not re.fullmatch('[a-f0-9]{16}', sample['source_fingerprint']) or
                    any(not _finite(v) for v in sample['timings'].values()) or
                    any(type(sample['coverage'][k]) is not int or sample['coverage'][k] < 0 for k in ('files', 'bytes'))):
                sample['state'] = 'incomplete'
            sample['timings'] = {k: v if _finite(v) else None for k, v in sample['timings'].items()}
            # Retained observations are read once into the final snapshot, never
            # concatenated across repeated reads of the same history.
            phases = value.get('activation', {}).get('phases', {})
            retained = {name: health._summary(phases[name].get('samples_ms', [])[-32:]) for name in
                        ('SessionStart', 'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'Stop') if name in phases}
            saved = value['timings'].get('automatic_commands', {})
            if (type(saved.get('samples')) is int and 0 <= saved['samples'] <= 32 and
                    all(saved.get(k) is None or _finite(saved[k]) for k in ('median_ms', 'p95_ms'))):
                command_times = {k: saved.get(k) for k in ('samples', 'median_ms', 'p95_ms')}
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            sample['error'] = type(exc).__name__
        sample['elapsed_ms'] = round((time.monotonic() - begin) * 1000, 3)
        if time.monotonic() >= deadline:
            sample['state'] = 'incomplete'
        samples.append(sample)
    moved = fingerprint() != runtime or len({s['source_fingerprint'] for s in samples if s['source_fingerprint']}) > 1
    complete = len(samples) == repeats and not moved and all(s['state'] == 'complete' for s in samples)
    return {'schema_version': 1, 'kind': 'health_performance', 'host': host,
            'generated_at': datetime.now(timezone.utc).isoformat(), 'runtime_fingerprint': runtime,
            'python': sys.version.split()[0], 'os': platform.system(), 'os_release': platform.release(),
            'warmup': 'none; every attempted read retained', 'requested': repeats, 'attempted': len(samples),
            'budget_seconds': timeout, 'elapsed_ms': round((time.monotonic() - started) * 1000, 3),
            'state': 'complete' if complete else 'incomplete', 'inputs_changed': moved, 'samples': samples,
            'retained_callbacks': retained, 'retained_command_distribution': command_times,
            'read_distribution': health._summary([s['elapsed_ms'] for s in samples]),
            'limits': ['Descriptive local sample, not universal latency, model speedup or improved coding evidence.',
                       'No checks, host or engine are launched; an in-flight read may exceed the cooperative deadline.',
                       'Callback samples exclude host launch and final registry write; Stop can include verification time.',
                       'Retained callback and command samples describe prior execution, separately from current reads.']}


def render(value):
    lines = ['# ElevenPowers health performance', '',
             f"Host: {value['host']}; measurement: {value['state']}; reads: {value['attempted']}/{value['requested']}",
             f"Runtime: `{value['runtime_fingerprint']}`", f"Warmup: {value['warmup']}", '',
             '| Read | State | Health | Files | Bytes | Elapsed ms |', '|---|---|---|---|---|---|']
    lines += [f"| {i} | {s['state']} | {s['health_state']} | {s['coverage']['files']} | {s['coverage']['bytes']} | {s['elapsed_ms']} |"
              for i, s in enumerate(value['samples'], 1)]
    lines += ['', f"Read distribution: {value['read_distribution']}",
              f"Retained callbacks: {value['retained_callbacks']}", f"Retained commands: {value['retained_command_distribution']}", '']
    return '\n'.join([*lines, *['Limit: ' + limit for limit in value['limits']], ''])
