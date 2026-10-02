"""Bounded read-only health sampling; every attempted read remains visible."""
from datetime import datetime, timezone
import math
from pathlib import Path
import platform
import sys
import time

from .. import health
from .provenance import fingerprint
from .setup import PATHS


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
            'read_distribution': health._summary([s['elapsed_ms'] for s in samples]),
            'limits': ['Descriptive local sample, not universal latency, model speedup or improved coding evidence.',
                       'No checks, host or engine are launched; an in-flight read may exceed the cooperative deadline.']}
