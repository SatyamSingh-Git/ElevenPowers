"""Which v3 stages are covered by the certified rules, which are not, and which are self-contained. $0.

Certification is the acted-on experiment's simulated perfect reviewer. Usage: stage_scan.py <new scratch dir>."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from eval.multistage_cases import load, tree  # noqa: E402
from eval.rule_groups_run import _sources, certify  # noqa: E402

CASES = ROOT / 'eval' / 'multistage_v3'
scratch = Path(sys.argv[1])
rows = []
for folder in sorted(p for p in CASES.iterdir() if (p / 'case.json').exists()):
    case = load(folder)
    entries = certify(case, scratch / case['id'] / 'certify')
    declared = [frozenset(e['inputs']) for e in entries]
    inputs = {p for e in entries for p in e['inputs']}
    for n, stage in enumerate(case['stages'], 1):
        before = _sources(tree(case, n - 1, scratch / case['id'] / f'{n}-before'))
        after = _sources(tree(case, n, scratch / case['id'] / f'{n}-after'))
        changed = {p for p in after if before.get(p) != after[p]} | (set(before) - set(after))
        quiet = stage.get('quiet') or []
        if quiet:
            covered = any(any(q['file'] in d and (d - {q['file']}) & changed for d in declared) for q in quiet)
            kind = 'covered' if covered else 'uncovered'
        else:
            kind = 'self-contained'
        rows.append({'case': case['id'], 'stage': n, 'kind': kind, 'declared_rules': len(entries),
                     'reference_touches_declared': sorted(changed & inputs)})
        print(json.dumps(rows[-1]), flush=True)
Path(__file__).with_name('stage-scan.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
