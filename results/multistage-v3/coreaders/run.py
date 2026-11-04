"""The token spike's three evaluations, with the co-readers scorer: the 31 losses,
the held-out dependents, and noise over every stage. Loops follow rank.py,
heldout.py and noise.py; results are written here, not over theirs."""
import json
from pathlib import Path

from coreaders import scored
from rank import BATCHES, ROOT, V3, sources

HERE = Path(__file__).resolve().parent
THRESHOLDS = (0, .05, .1, .15, .2, .3, .4, .5)


def place(before, after, edited, dependent):
    scores = scored(before, after, edited)[0]
    order = [path for _, path in scores]
    return (order.index(dependent) + 1 if dependent in order else None), len(order)


def edits(folder, n):
    old, new = sources(folder / str(n - 1)), sources(folder / str(n))
    return [p for p in new if old.get(p) != new[p]]


def case(name):
    return json.loads((ROOT / 'eval' / 'multistage_v3' / name / 'case.json').read_text(encoding='utf-8'))


def quiet_of(stage):
    quiet = stage.get('quiet') or []
    return quiet if isinstance(quiet, list) else [quiet]


def tops(rows, key='rank'):
    return {k: sum(r[key] is not None and r[key] <= k for r in rows) for k in (1, 3, 5)}


def main():
    rerun = set(json.loads((V3 / 'full-rerun-c.json').read_text(encoding='utf-8')))
    folder_of = lambda slot: BATCHES['c' if slot in rerun else 'b'] / slot / 'snapshots'  # noqa: E731
    losses = json.loads((V3 / 'diagnosis-elevenpowers-losses.json').read_text(encoding='utf-8'))

    in_sample = []
    for loss in losses:
        folder, n = folder_of(loss['slot']), loss['stage']
        stages = case(loss['slot'].split('--')[0])['stages']
        other = n + 1 if (folder / str(n + 1)).exists() else n - 1
        for dependent in loss['dependent']:
            rank, of = place(folder / str(n - 1), folder / str(n), loss['agent_edited'], dependent)
            control = place(folder / str(other - 1), folder / str(other), edits(folder, other), dependent)[0]
            kind = next((q['kind'] for q in quiet_of(stages[n - 1]) if q['file'] == dependent), '?')
            in_sample.append({'slot': loss['slot'], 'stage': n, 'dependent': dependent, 'kind': kind,
                              'rank': rank, 'of': of, 'control_rank': control})

    analysis = json.loads((V3 / 'full-analysis.json').read_text(encoding='utf-8'))
    seen = {(l['slot'].split('--')[0], l['stage']) for l in losses}
    held_out, noise = [], []
    for row in analysis['rows']:
        stages = case(row['case'])['stages']
        folder = folder_of(row['slot'])
        for n, stage in enumerate(stages, 1):
            if not (folder / str(n)).exists():
                continue
            before, after = folder / str(n - 1), folder / str(n)
            edited = edits(folder, n)
            scores, total, _, _, _ = scored(before, after, edited)
            dependents = sorted({q['file'] for q in quiet_of(stage)} - set(edited))
            noise.append({'slot': row['slot'], 'stage': n, 'kind': stage['kind'], 'dependents': dependents,
                          'top': [[round(s / total, 4) if total else 0, p] for s, p in scores[:10]]})
            if (row['case'], n) in seen or not quiet_of(stage):
                continue
            other = n + 1 if n < len(stages) else n - 1
            other_edited = edits(folder, other)
            for dependent in dependents:
                order = [p for _, p in scores]
                control = (place(folder / str(other - 1), folder / str(other), other_edited, dependent)[0]
                           if dependent not in other_edited else None)
                held_out.append({'slot': row['slot'], 'stage': n, 'dependent': dependent,
                                 'kind': next(q['kind'] for q in quiet_of(stage) if q['file'] == dependent),
                                 'rank': order.index(dependent) + 1 if dependent in order else None,
                                 'of': len(order), 'control_rank': control})

    (HERE / 'results.json').write_text(json.dumps({'in_sample': in_sample, 'held_out': held_out, 'noise': noise},
                                                  indent=1), encoding='utf-8')
    for name, rows in (('in-sample losses', in_sample), ('held-out', held_out)):
        print(f"{name}: {len(rows)} rankings; top 1/3/5 {tops(rows)}; control {tops(rows, 'control_rank')}; "
              f"random top 3 {sum(3 / r['of'] for r in rows):.1f}")
        for kind in sorted({r['kind'] for r in rows}):
            sub = [r for r in rows if r['kind'] == kind]
            print(f"   {kind:9} {len(sub):3}  top 3 {tops(sub)[3]}  control {tops(sub, 'control_rank')[3]}")
    plain = [r for r in noise if r['kind'] == 'self-contained']
    crossing = [r for r in noise if r['kind'] == 'cross-cutting']
    wanted = sum(len(r['dependents']) for r in crossing)
    print(f'noise: {len(noise)} stages, {len(plain)} self-contained, {len(crossing)} cross-cutting, '
          f'{wanted} unedited dependents')
    print('t     warns(self-contained)  warns(cross-cutting)  dependents named  named that are dependents')
    for t in THRESHOLDS:
        def named(r):
            return [path for share, path in r['top'][:3] if share >= t and share > 0]
        found = sum(len(set(named(r)) & set(r['dependents'])) for r in crossing)
        names = sum(len(named(r)) for r in crossing)
        print(f"{t:<5} {sum(bool(named(r)) for r in plain) / len(plain):>8.0%}"
              f" {sum(bool(named(r)) for r in crossing) / len(crossing):>20.0%}"
              f" {found:>12} of {wanted} ({found / wanted:.0%})"
              f" {found:>10} of {names} ({found / names if names else 0:.0%})")


if __name__ == '__main__':
    main()
