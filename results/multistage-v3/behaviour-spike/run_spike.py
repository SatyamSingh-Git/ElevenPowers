"""Run the behaviour-diff spike over v3 stages: every ElevenPowers-arm loss, plus clean stages for noise."""
from concurrent.futures import ThreadPoolExecutor
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from behaviour_diff import stage

ANALYSIS = json.loads(pathlib.Path('E:/ElevenPowers/results/multistage-v3/full-analysis.json').read_text(encoding='utf-8'))
RERUN = set(json.loads(pathlib.Path('E:/ElevenPowers/results/multistage-v3/full-rerun-c.json').read_text(encoding='utf-8')))
mode, out = sys.argv[1], pathlib.Path(sys.argv[2])
limit = int(sys.argv[3]) if len(sys.argv) > 3 else None


def folder(slot):
    return pathlib.Path(f"E:/ep-runs/multistage-v3-full-2026-10-30-{'c' if slot in RERUN else 'b'}/{slot}")


jobs = []
for row in ANALYSIS['rows']:
    case = json.loads(pathlib.Path(f"E:/ElevenPowers/eval/multistage_v3/{row['case']}/case.json").read_text(encoding='utf-8'))
    for graded in row['grade']['stages']:
        n = graded['stage']
        quiet = case['stages'][n - 1].get('quiet') or []
        quiet = quiet if isinstance(quiet, list) else [quiet]
        lost = bool(graded['lost'])
        if mode == 'losses' and lost and row['arm'] == 'elevenpowers':
            jobs.append((row['slot'], n, case, [q['file'] for q in quiet], True))
        if mode == 'clean' and not lost and row['replicate'] == 0:
            jobs.append((row['slot'], n, case, [q['file'] for q in quiet], False))
jobs = jobs[:limit]


def one(job):
    slot, n, case, dependents, lost = job
    base = folder(slot) / 'snapshots'
    result = stage(base / str(n - 1), base / str(n), case)
    result.update(slot=slot, stage=n, lost=lost, dependents=dependents,
                  caught=bool(dependents) and any(d in result['flagged'] for d in dependents))
    print(slot, n, 'caught' if result['caught'] else '-', 'flagged', len(result['flagged']), flush=True)
    return result


with ThreadPoolExecutor(4) as pool:
    results = list(pool.map(one, jobs))
out.write_text(json.dumps(results, indent=1), encoding='utf-8')
