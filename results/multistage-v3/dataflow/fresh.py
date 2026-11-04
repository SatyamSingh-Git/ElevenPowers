"""Rank the 51 never-read declared dependents from each case's own reference, with
three scorers on the same trees: shared rare tokens, co-readers and data flow.
The stages behind the losses and the earlier held-out set are excluded."""
import json
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
ROOT = V3.parents[1]
for folder in ('convention-spike', 'coreaders'):
    sys.path.insert(0, str(V3 / folder))
sys.path.insert(0, str(ROOT))
import coreaders  # noqa: E402
import dataflow  # noqa: E402
import rank  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402

SCORERS = {'tokens': rank.scored, 'coreaders': coreaders.scored, 'dataflow': dataflow.scored}


def seen_stages():
    losses = json.loads((V3 / 'diagnosis-elevenpowers-losses.json').read_text(encoding='utf-8'))
    held = json.loads((V3 / 'coreaders' / 'results.json').read_text(encoding='utf-8'))['held_out']
    return {(r['slot'].split('--')[0], r['stage']) for r in losses + held}


def edits(before, after):
    old, new = rank.sources(before), rank.sources(after)
    return [p for p in new if old.get(p) != new[p]]


def place(scorer, before, after, edited, dependent):
    order = [path for _, path in scorer(before, after, edited)[0]]
    return order.index(dependent) + 1 if dependent in order else None, len(order)


def main():
    seen = seen_stages()
    rows = []
    scratch = Path(tempfile.mkdtemp(prefix='ep-dataflow-'))
    try:
        for root in sorted((ROOT / 'eval' / 'multistage_v3').iterdir()):
            if not (root / 'case.json').exists():
                continue
            case = load(root)
            built = {}

            def made(stage, variant='reference', which=0):
                key = (stage, variant, which)
                if key not in built:
                    built[key] = tree(case, stage, scratch / f"{case['id']}-{stage}-{variant}-{which}", variant, which)
                return built[key]
            stages = case['stages']
            for n, stage in enumerate(stages, 1):
                if (case['id'], n) in seen:
                    continue
                for which, quiet in enumerate(stage.get('quiet') or []):
                    before, after = made(n - 1), made(n, 'quiet', which)
                    edited = edits(before, after)
                    other = next(m for m in (n + 1, n - 1, n + 2, n - 2) if 1 <= m <= len(stages) and m != n)
                    o_before, o_after = made(other - 1), made(other)
                    o_edited = edits(o_before, o_after)
                    row = {'case': case['id'], 'stage': n, 'dependent': quiet['file'], 'kind': quiet['kind']}
                    for name, scorer in SCORERS.items():
                        row[name], row['of'] = place(scorer, before, after, edited, quiet['file'])
                        row[name + '_control'] = (place(scorer, o_before, o_after, o_edited, quiet['file'])[0]
                                                  if quiet['file'] not in o_edited else None)
                    rows.append(row)
                    print(row)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    (HERE / 'fresh.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    print(len(rows), 'never-read dependents')
    for name in SCORERS:
        top = {k: sum(r[name] is not None and r[name] <= k for r in rows) for k in (1, 3, 5)}
        control = sum(r[name + '_control'] is not None and r[name + '_control'] <= 3 for r in rows)
        kinds = {kind: sum(r[name] is not None and r[name] <= 3 for r in rows if r['kind'] == kind)
                 for kind in sorted({r['kind'] for r in rows})}
        print(f'{name:10} top 1/3/5 {top}  control top 3 {control}  top 3 by kind {kinds}')
    print('random, top 3:', round(sum(3 / r['of'] for r in rows), 1))


if __name__ == '__main__':
    main()
