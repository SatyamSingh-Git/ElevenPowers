"""The same ranking on the dependents the method was not designed from.

Every v3 stage declares quiet dependents, but only the twelve (case, stage)
pairs behind the 31 losses were read before rank.py was written. Here every
other declared dependent is ranked with each conversation's own edit of that
stage, both arms, against the same control: another stage's edit.
"""
import json
from pathlib import Path

from rank import BATCHES, ROOT, V3, rank, sources


def main():
    analysis = json.loads((V3 / 'full-analysis.json').read_text(encoding='utf-8'))
    rerun = set(json.loads((V3 / 'full-rerun-c.json').read_text(encoding='utf-8')))
    seen = {(l['slot'].split('--')[0], l['stage'])
            for l in json.loads((V3 / 'diagnosis-elevenpowers-losses.json').read_text(encoding='utf-8'))}
    rows = []
    for row in analysis['rows']:
        case = json.loads((ROOT / 'eval' / 'multistage_v3' / row['case'] / 'case.json').read_text(encoding='utf-8'))
        folder = BATCHES['c' if row['slot'] in rerun else 'b'] / row['slot'] / 'snapshots'
        stages = len(case['stages'])
        for n in range(1, stages + 1):
            quiet = case['stages'][n - 1].get('quiet') or []
            quiet = quiet if isinstance(quiet, list) else [quiet]
            if (row['case'], n) in seen or not quiet or not (folder / str(n)).exists():
                continue
            before, after = folder / str(n - 1), folder / str(n)
            old, new = sources(before), sources(after)
            edited = [p for p in new if old.get(p) != new[p]]
            other = n + 1 if n < stages else n - 1
            o_old, o_new = sources(folder / str(other - 1)), sources(folder / str(other))
            other_edited = [p for p in o_new if o_old.get(p) != o_new[p]]
            for dependent in {q['file'] for q in quiet}:
                if dependent in edited:
                    continue  # the agent changed it itself; nothing was left behind
                place, of, _ = rank(before, after, edited, dependent)
                control = rank(folder / str(other - 1), folder / str(other), other_edited, dependent)[0] \
                    if dependent not in other_edited else None
                rows.append({'slot': row['slot'], 'stage': n, 'dependent': dependent, 'kind': next(
                    q['kind'] for q in quiet if q['file'] == dependent), 'rank': place, 'of': of, 'control_rank': control})
    Path(__file__).with_name('heldout.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    pairs = {(r['slot'].split('--')[0], r['stage'], r['dependent']) for r in rows}
    print(len(rows), 'rankings of', len(pairs), 'held-out dependents')
    for k in (1, 3, 5):
        hit = sum(r['rank'] is not None and r['rank'] <= k for r in rows)
        ctl = sum(r['control_rank'] is not None and r['control_rank'] <= k for r in rows)
        print(f'top {k}: {hit} of {len(rows)} ({hit / len(rows):.0%}) | control {ctl} ({ctl / len(rows):.0%})')
    print('random, top 3:', f"{sum(3 / r['of'] for r in rows) / len(rows):.0%}")
    for kind in sorted({r['kind'] for r in rows}):
        sub = [r for r in rows if r['kind'] == kind]
        print(kind, len(sub), 'top 3:', f"{sum(r['rank'] is not None and r['rank'] <= 3 for r in sub) / len(sub):.0%}")


if __name__ == '__main__':
    main()
