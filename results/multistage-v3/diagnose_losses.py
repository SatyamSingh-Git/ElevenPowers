import filecmp
import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, 'E:/ElevenPowers')
from core.atlas import neighbourhood, source_model

analysis = json.loads(pathlib.Path('E:/ElevenPowers/results/multistage-v3/full-analysis.json').read_text(encoding='utf-8'))
rerun = set(json.loads(pathlib.Path('E:/ElevenPowers/results/multistage-v3/full-rerun-c.json').read_text(encoding='utf-8')))
batches = {'b': pathlib.Path('E:/ep-runs/multistage-v3-full-2026-10-30-b'),
           'c': pathlib.Path('E:/ep-runs/multistage-v3-full-2026-10-30-c')}
arm = sys.argv[1] if len(sys.argv) > 1 else 'elevenpowers'


def edited(before, after):
    changed = []
    for path in after.rglob('*.py'):
        rel = path.relative_to(after)
        other = before / rel
        if not other.exists() or not filecmp.cmp(path, other, shallow=False):
            changed.append(rel.as_posix())
    return changed


rows, tally = [], Counter()
for row in analysis['rows']:
    if row['arm'] != arm:
        continue
    case = json.loads(pathlib.Path(f"E:/ElevenPowers/eval/multistage_v3/{row['case']}/case.json").read_text(encoding='utf-8'))
    folder = (batches['c'] if row['slot'] in rerun else batches['b']) / row['slot']
    for stage in row['grade']['stages']:
        if not stage['lost']:
            continue
        n = stage['stage']
        quiet = case['stages'][n - 1].get('quiet') or []
        quiet = quiet if isinstance(quiet, list) else [quiet]
        targets = {q['file'] for q in quiet}
        before, after = folder / 'snapshots' / str(n - 1), folder / 'snapshots' / str(n)
        changes = edited(before, after)
        model = source_model(before)
        briefs = {f: neighbourhood(before, f, model) for f in changes if f not in targets}
        detected = any(t in brief for brief in briefs.values() for t in targets)
        transcript = (folder / f'native-{n}.jsonl').read_text(encoding='utf-8')
        delivered = 'imported by' in transcript and any(t in transcript.split('imported by', 1)[1] for t in targets)
        touched = any(t in changes for t in targets)
        opened = any(t in transcript for t in targets)
        verdict = ('not detected' if not detected else 'detected, not delivered' if not delivered
                   else 'delivered, ignored')
        tally[verdict] += 1
        tally['agent edited the dependent'] += touched
        tally['agent mentioned/opened the dependent'] += opened
        rows.append({'slot': row['slot'], 'stage': n, 'lost': stage['lost'], 'dependent': sorted(targets),
                     'agent_edited': changes, 'verdict': verdict, 'briefs': briefs,
                     'dependent_edited': touched, 'dependent_seen_in_transcript': opened})
print(arm, dict(tally))
out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None
if out:
    out.write_text(json.dumps(rows, indent=1), encoding='utf-8')
for r in rows[:6]:
    print(r['slot'], r['stage'], r['dependent'], r['verdict'], {k: v[:160] for k, v in r['briefs'].items()})
