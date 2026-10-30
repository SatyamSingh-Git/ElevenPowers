"""The pre-registered analysis of a multi-stage run, frozen in results/multistage-v3/manifest.json.

A case's difference is mean(superpowers) - mean(superpowers+ElevenPowers) over
its comparable conversations, so positive means fewer with ElevenPowers. Cases
enter the exact two-sided signed-rank test; Holm runs across the two
co-primaries. A conversation that is not comparable is reported missing, never
counted as zero. A continuation batch fills only the slots its first batch did
not complete.
"""
import argparse
import json
from pathlib import Path

from .multistage_power import exact_signed_rank
from .multistage_run import collect

OUTCOMES = ('lost', 'stale')


def merge(first, continuation):
    later = {row['slot']: row for row in continuation}
    return [row if row['comparable'] else later.get(row['slot'], row) for row in first]


def _outcome(rows, name):
    by_case = {}
    for row in rows:
        by_case.setdefault(row['case'], {}).setdefault(row['arm'], []).append(row[name])
    cases = {case: sum(arms['superpowers']) / len(arms['superpowers'])
             - sum(arms['elevenpowers']) / len(arms['elevenpowers'])
             for case, arms in sorted(by_case.items()) if len(arms) == 2}
    totals = {arm: sum(row[name] for row in rows if row['arm'] == arm) for arm in ('superpowers', 'elevenpowers')}
    return {'totals': totals, 'cases': cases, 'better': sum(d > 0 for d in cases.values()),
            'worse': sum(d < 0 for d in cases.values()), 'tied': sum(d == 0 for d in cases.values()),
            'p': exact_signed_rank(list(cases.values()))}


def analyse(rows):
    comparable = [row for row in rows if row['comparable']]
    outcomes = {name: _outcome(comparable, name) for name in OUTCOMES}
    first, second = sorted(OUTCOMES, key=lambda name: outcomes[name]['p'])
    outcomes[first]['p_holm'] = min(1.0, 2 * outcomes[first]['p'])
    outcomes[second]['p_holm'] = max(outcomes[first]['p_holm'], outcomes[second]['p'])
    missing = {arm: sum(1 for row in rows if row['arm'] == arm and not row['comparable'])
               for arm in ('superpowers', 'elevenpowers')}
    return {'conversations': {'scheduled': len(rows), 'comparable': len(comparable), 'missing': missing},
            'outcomes': outcomes}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--continuation', type=Path)
    parser.add_argument('--regrade', action='store_true', help='grade again from the kept snapshots')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    rows = collect(args.batch, regrade=args.regrade)
    if args.continuation:
        rows = merge(rows, collect(args.continuation, regrade=args.regrade))
    result = {'rows': rows, **analyse(rows)}
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('conversations', 'outcomes')}, indent=2))


if __name__ == '__main__':
    main()
