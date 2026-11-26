"""The held-out comparison's analysis, fixed before any paid run.

Primary: per task, the fraction of resolved runs that are VACUOUS in each arm;
the two-sided Wilcoxon signed-rank test over tasks of (ordinary - assisted).
Tasks where either arm resolved nothing are dropped and counted; tied tasks are
counted. Replicates are aggregated per task and never treated as tasks.
Secondary figures are reported beside the primary, never in its place.
"""
import argparse
import json
from pathlib import Path

from .vacuity_power import _sign_test, _signed_rank

ARMS = ('ordinary', 'assisted')
# docs/superpowers/specs/2026-11-26-heldout-four-arms-design.md: five primaries, Holm-adjusted together.
FOUR_ARMS = ('ordinary', 'instructed', 'superpowers', 'assisted')
PAIRS = (('ordinary', 'instructed'), ('ordinary', 'superpowers'), ('instructed', 'assisted'),
         ('superpowers', 'assisted'), ('ordinary', 'assisted'))


def _by_task(graded, arms):
    tasks = {}
    for record in graded:
        if record['arm'] in arms:
            tasks.setdefault(record['task'], {arm: [] for arm in arms})[record['arm']].append(record)
    return tasks


def compare(records, first, second):
    """The signed-rank over tasks of `first` - `second` vacuous fraction among resolved, and resolve beside it."""
    tasks = _by_task([r for r in records if r['state'] == 'graded'], (first, second))
    differences, tied, dropped = {}, 0, 0
    resolve_better = {f'{second}_better': 0, f'{first}_better': 0, 'tied': 0}
    for task, arms in sorted(tasks.items()):
        rates = {arm: sum(r['resolved'] for r in runs) / len(runs) if runs else None for arm, runs in arms.items()}
        if None not in rates.values():
            key = (f'{second}_better' if rates[second] > rates[first] else
                   f'{first}_better' if rates[first] > rates[second] else 'tied')
            resolve_better[key] += 1
        resolved = {arm: [r for r in runs if r['resolved']] for arm, runs in arms.items()}
        if not all(resolved.values()):
            dropped += 1
            continue
        fraction = {arm: sum(bool(r['vacuous']) for r in runs) / len(runs) for arm, runs in resolved.items()}
        difference = fraction[first] - fraction[second]
        if difference == 0:
            tied += 1
        else:
            differences[task] = difference
    return {'test': f'two-sided Wilcoxon signed-rank over tasks, {first} - {second} vacuous fraction',
            'differences': differences, 'tied': tied, 'dropped_unresolved': dropped,
            'p': _signed_rank(list(differences.values())),
            'resolve': {**resolve_better, 'p': _sign_test(resolve_better[f'{second}_better'],
                                                          resolve_better[f'{first}_better'])}}


def holm(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    adjusted, running = [0.0] * len(values), 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, values[index] * (len(values) - rank)))
        adjusted[index] = running
    return adjusted


def _runs(records, graded):
    return {'scheduled': len(records), 'graded': len(graded), 'incomplete': len(records) - len(graded)}


def _per_arm(graded, arms):
    by_arm = {arm: [r for r in graded if r['arm'] == arm] for arm in arms}
    return {'mean_seconds': {arm: sum(r['seconds'] for r in runs) / len(runs) if runs else None
                             for arm, runs in by_arm.items()},
            'total_cost': {arm: round(sum(r['cost'] or 0 for r in runs), 4) for arm, runs in by_arm.items()}}


def analyse(records):
    graded = [r for r in records if r['state'] == 'graded']
    pair = compare(records, 'ordinary', 'assisted')
    resolve = pair.pop('resolve')
    return {'runs': _runs(records, graded), 'tasks': len(_by_task(graded, ARMS)),
            'primary': pair, 'secondary': {'resolve': resolve, **_per_arm(graded, ARMS)}}


def four(records):
    graded = [r for r in records if r['state'] == 'graded']
    pairs = {f'{a} - {b}': compare(records, a, b) for a, b in PAIRS}
    for value, adjusted in zip(pairs.values(), holm([value['p'] for value in pairs.values()])):
        value['holm_p'] = adjusted
    resolved = {arm: [r for r in graded if r['arm'] == arm and r['resolved']] for arm in FOUR_ARMS}
    return {'runs': _runs(records, graded), 'tasks': len(_by_task(graded, FOUR_ARMS)),
            'primary': pairs,
            'secondary': {'resolved_changing_a_test': {arm: {'resolved': len(runs),
                                                            'changing_a_test': sum(bool(r.get('changes_test')) for r in runs)}
                                                      for arm, runs in resolved.items()},
                          **_per_arm(graded, FOUR_ARMS)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path, help='a JSON list of run records')
    parser.add_argument('--four-arms', action='store_true', help='the 2026-11-26 study: five pairs, Holm-adjusted')
    args = parser.parse_args()
    records = json.loads(args.results.read_text(encoding='utf8'))
    print(json.dumps(four(records) if args.four_arms else analyse(records), indent=2))


if __name__ == '__main__':
    main()
