"""How often would the token ranking warn when nothing was left behind?

Every stage of every v3 conversation is ranked with its own edit. On the 33
self-contained stages any warning is a false alarm; on cross-cutting stages a
declared quiet dependent the agent left unedited should be named. The plan
was stated in README.md before this ran.
"""
import json
from pathlib import Path

from rank import BATCHES, ROOT, V3, scored, sources

THRESHOLDS = (0, .05, .1, .15, .2, .3, .4, .5)
NAMED = 3


def main():
    analysis = json.loads((V3 / 'full-analysis.json').read_text(encoding='utf-8'))
    rerun = set(json.loads((V3 / 'full-rerun-c.json').read_text(encoding='utf-8')))
    rows = []
    for row in analysis['rows']:
        case = json.loads((ROOT / 'eval' / 'multistage_v3' / row['case'] / 'case.json').read_text(encoding='utf-8'))
        folder = BATCHES['c' if row['slot'] in rerun else 'b'] / row['slot'] / 'snapshots'
        for n, stage in enumerate(case['stages'], 1):
            if not (folder / str(n)).exists():
                continue
            before, after = folder / str(n - 1), folder / str(n)
            old, new = sources(before), sources(after)
            edited = [p for p in new if old.get(p) != new[p]]
            scores, total, _, _, _ = scored(before, after, edited)
            quiet = stage.get('quiet') or []
            quiet = quiet if isinstance(quiet, list) else [quiet]
            rows.append({'slot': row['slot'], 'stage': n, 'kind': stage['kind'], 'edited': edited,
                         'dependents': sorted({q['file'] for q in quiet} - set(edited)),
                         'top': [[round(score / total, 4) if total else 0, path] for score, path in scores[:10]]})
    Path(__file__).with_name('noise.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    plain = [r for r in rows if r['kind'] == 'self-contained']
    crossing = [r for r in rows if r['kind'] == 'cross-cutting']
    wanted = sum(len(r['dependents']) for r in crossing)
    print(len(rows), 'stages ranked:', len(plain), 'self-contained,', len(crossing), 'cross-cutting with',
          wanted, 'unedited dependents')
    print('t     warns(self-contained)  warns(cross-cutting)  dependents named  named that are dependents')
    for t in THRESHOLDS:
        def named(r):
            return [path for share, path in r['top'][:NAMED] if share >= t and share > 0]
        found = sum(len(set(named(r)) & set(r['dependents'])) for r in crossing)
        names = sum(len(named(r)) for r in crossing)
        print(f"{t:<5} {sum(bool(named(r)) for r in plain) / len(plain):>8.0%}"
              f" {sum(bool(named(r)) for r in crossing) / len(crossing):>20.0%}"
              f" {found:>12} of {wanted} ({found / wanted:.0%})"
              f" {found:>10} of {names} ({found / names if names else 0:.0%})")


if __name__ == '__main__':
    main()
