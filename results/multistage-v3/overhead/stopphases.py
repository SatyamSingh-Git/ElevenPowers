"""Time the Stop runs the v3 conversations actually made, from each conversation's
verification.json. A run that contains a "test strength" phase is a Stop: nothing
else starts that analysis. Prints per-run spans and phase times, and why the
strength analysis ended as it did. Same conversations as overhead.py."""
import collections
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[3]
V3 = ROOT / 'results' / 'multistage-v3'
BATCHES = {'b': Path('E:/ep-runs/multistage-v3-full-2026-10-30-b'), 'c': Path('E:/ep-runs/multistage-v3-full-2026-10-30-c')}

analysis = json.loads((V3 / 'full-analysis.json').read_text(encoding='utf-8'))
rerun = set(json.loads((V3 / 'full-rerun-c.json').read_text(encoding='utf-8')))
spans, phases, reasons = [], collections.defaultdict(list), collections.Counter()
conversations = missing = 0
for row in analysis['rows']:
    if row['arm'] != 'elevenpowers':
        continue
    conversations += 1
    path = BATCHES['c' if row['slot'] in rerun else 'b'] / row['slot'] / 'work/.elevenpowers/verification.json'
    if not path.exists():
        missing += 1
        continue
    runs = collections.defaultdict(list)
    for check in json.loads(path.read_text(encoding='utf-8'))['checks']:
        if check.get('started') and check.get('finished'):
            runs[check['run']].append(check)
    for checks in runs.values():
        if not any(c['phase'] == 'test strength' for c in checks):
            continue
        spans.append(max(c['finished'] for c in checks) - min(c['started'] for c in checks))
        by = collections.Counter()
        for c in checks:
            by[c['phase']] += c['finished'] - c['started']
            if c['phase'] == 'test strength':
                reasons[c.get('reason', '').split(':')[0][:70] or '(none)'] += 1
        for phase in ('working tree inspection', 'baseline preparation', 'baseline', 'confirmation', 'test strength'):
            phases[phase].append(by[phase])

print(f'{conversations} ElevenPowers conversations, {missing} without verification.json, {len(spans)} Stop runs')
print(f'Stop run span: median {statistics.median(spans):.1f} s, mean {statistics.mean(spans):.1f} s, max {max(spans):.1f} s')
for phase, values in phases.items():
    print(f'  {phase:24} median {statistics.median(values):5.2f} s  mean {statistics.mean(values):5.2f} s')
print('test strength ended because:')
for reason, count in reasons.most_common():
    print(f'  {count:4}  {reason}')
