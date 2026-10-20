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


def _by_task(graded):
    tasks = {}
    for record in graded:
        tasks.setdefault(record['task'], {arm: [] for arm in ARMS})[record['arm']].append(record)
    return tasks


def analyse(records):
    graded = [r for r in records if r['state'] == 'graded']
    tasks = _by_task(graded)
    differences, tied, dropped = {}, 0, 0
    resolve_better = {'assisted_better': 0, 'ordinary_better': 0, 'tied': 0}
    for task, arms in sorted(tasks.items()):
        rates = {arm: sum(r['resolved'] for r in runs) / len(runs) if runs else None for arm, runs in arms.items()}
        if None not in rates.values():
            key = ('assisted_better' if rates['assisted'] > rates['ordinary'] else
                   'ordinary_better' if rates['ordinary'] > rates['assisted'] else 'tied')
            resolve_better[key] += 1
        resolved = {arm: [r for r in runs if r['resolved']] for arm, runs in arms.items()}
        if not all(resolved.values()):
            dropped += 1
            continue
        fraction = {arm: sum(bool(r['vacuous']) for r in runs) / len(runs) for arm, runs in resolved.items()}
        difference = fraction['ordinary'] - fraction['assisted']
        if difference == 0:
            tied += 1
        else:
            differences[task] = difference
    by_arm = {arm: [r for r in graded if r['arm'] == arm] for arm in ARMS}
    return {
        'runs': {'scheduled': len(records), 'graded': len(graded), 'incomplete': len(records) - len(graded)},
        'tasks': len(tasks),
        'primary': {'test': 'two-sided Wilcoxon signed-rank over tasks, ordinary - assisted vacuous fraction',
                    'differences': differences, 'tied': tied, 'dropped_unresolved': dropped,
                    'p': _signed_rank(list(differences.values()))},
        'secondary': {
            'resolve': {**resolve_better, 'p': _sign_test(resolve_better['assisted_better'], resolve_better['ordinary_better'])},
            'mean_seconds': {arm: sum(r['seconds'] for r in runs) / len(runs) if runs else None for arm, runs in by_arm.items()},
            'total_cost': {arm: round(sum(r['cost'] or 0 for r in runs), 4) for arm, runs in by_arm.items()},
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path, help='a JSON list of run records')
    print(json.dumps(analyse(json.loads(parser.parse_args().results.read_text(encoding='utf8'))), indent=2))


if __name__ == '__main__':
    main()
