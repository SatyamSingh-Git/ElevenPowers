"""Rehearse multi-stage v2 cases with no model: the reference and three broken variants.

A case is usable only if, at every stage, the reference passes its groups,
documents its facts and keeps the rules, and each broken variant is caught by
the oracle meant to catch it: a missed dependent by the earlier groups it
names, forgotten docs by exactly the facts the stage changed, and doing
nothing by the stage's new groups.
"""
import argparse
from pathlib import Path
import sys
import tempfile

from .multistage_cases import PROFILES, load, tree
from .multistage_oracles import groups, rules, stale
from .multistage_quiet import changed_names, named, suite_passes
from .preservation import _write


def _passed(results):
    return bool(results) and set(results.values()) == {'passed'}


def rehearse(root, work):
    case, work = load(root), Path(work)
    start = tree(case, 0, work / '0-reference')
    found, docs = groups(case, 0, start), stale(case, 0, start)
    stages = [{'stage': 0, 'checks': {'reference_groups': _passed(found), 'reference_docs': docs == []},
               'detail': {'groups': found, 'stale': docs}}]
    previous = start
    for n, stage in enumerate(case['stages'], 1):
        reference = tree(case, n, work / f'{n}-reference')
        found, docs, kept = groups(case, n, reference), stale(case, n, reference), rules(case, n, previous, reference)
        checks = {'reference_groups': _passed(found), 'reference_docs': docs == [],
                  'reference_rules': kept['changelog'] >= 1 and kept['protected']
                  and (kept['test_with_fix'] is True or not stage['bugfix'])}
        detail = {'groups': found, 'stale': docs, 'rules': kept}
        if stage['kind'] == 'cross-cutting' and not PROFILES[case['profile']]['quiet']:
            missed = groups(case, n, tree(case, n, work / f'{n}-missed', 'dependent-missed'))
            earlier = {group['id'] for group in case['groups'] if group['since'] < n}
            detail['dependent_missed'] = sorted(g for g, state in missed.items() if state != 'passed' and g in earlier)
            checks['dependent_missed'] = detail['dependent_missed'] == sorted(stage['dependent_missed_fails'])
        if stage['kind'] == 'cross-cutting' and PROFILES[case['profile']]['quiet']:
            diff = (Path(case['root']) / 'stages' / str(n) / 'reference.diff').read_text(encoding='utf-8')
            earlier = {group['id'] for group in case['groups'] if group['since'] < n}
            detail['quiet'] = []
            for k, entry in enumerate(stage['quiet']):
                try:
                    left = tree(case, n, work / f'{n}-quiet-{k}', 'quiet', which=k)
                except ValueError as error:
                    checks[f'quiet_fails_{k}'] = False
                    detail['quiet'].append({'error': str(error)})
                    continue
                failing = sorted(g for g, state in groups(case, n, left).items() if state != 'passed' and g in earlier)
                dependent = previous / entry['file']
                found = (named(changed_names(diff, previous, entry['file']), dependent) if dependent.is_file()
                         else ['(the dependent does not exist before the stage)'])
                checks[f'quiet_fails_{k}'] = failing == sorted(entry['fails'])
                checks[f'quiet_suite_green_{k}'] = suite_passes(left, case)
                checks[f'quiet_unnamed_{k}'] = found == []
                detail['quiet'].append({'failing': failing, 'named': found})
        before, after = case['facts'][n - 1], case['facts'][n]
        changed = sorted({key for key in after if before.get(key) != after[key]} | (set(before) - set(after)))
        detail['docs_forgotten'] = stale(case, n, tree(case, n, work / f'{n}-forgotten', 'docs-forgotten'))
        checks['docs_forgotten'] = detail['docs_forgotten'] == changed
        nothing = groups(case, n, tree(case, n, work / f'{n}-no-op', 'no-op'))
        new = [group['id'] for group in case['groups'] if group['since'] == n]
        checks['no_op'] = all(nothing[g] != 'passed' for g in new)
        stages.append({'stage': n, 'checks': checks, 'detail': detail})
        previous = reference
    return {'id': case['id'], 'usable': all(all(s['checks'].values()) for s in stages), 'stages': stages}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--case', help='one case id; all cases when omitted')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    names = [args.case] if args.case else sorted(p.parent.name for p in args.cases.glob('*/case.json'))
    reports = {}
    for name in names:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as work:
            reports[name] = rehearse(args.cases / name, work)
        print(name, 'usable' if reports[name]['usable'] else 'NOT usable', flush=True)
    _write(args.out, reports)
    return 0 if reports and all(r['usable'] for r in reports.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
