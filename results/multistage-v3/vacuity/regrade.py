"""VACUOUS by arm on every stage of the v3 full run, from the kept snapshots ($0).

Pre-registered in README.md. The check per stage is the grader's own
`test_with_fix` code path (eval/multistage_oracles.rules), run on every stage
rather than bugfix stages only.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from eval.heldout_vacuity import vacuity  # noqa: E402
from eval.multistage_oracles import _patch  # noqa: E402
from eval.multistage_power import exact_signed_rank  # noqa: E402

HERE = Path(__file__).resolve().parent
ARMS = ('superpowers', 'elevenpowers')


def check(job):
    folder, case, n, strip_tests = job
    before, after = folder / 'snapshots' / str(n - 1), folder / 'snapshots' / str(n)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
        if strip_tests:
            # The adversarial control: the same stage with its test changes taken back out.
            stripped = Path(scratch) / 'after'
            shutil.copytree(after, stripped)
            shutil.rmtree(stripped / case['test_dir'], ignore_errors=True)
            if (before / case['test_dir']).exists():
                shutil.copytree(before / case['test_dir'], stripped / case['test_dir'])
            after = stripped
        patch = _patch(before, after, Path(scratch) / 'patch')
        return vacuity(before, patch, python=sys.executable, env={'PYTHONPATH': case['pythonpath']},
                       test_dir=case['test_dir'], work=Path(scratch) / 'vacuity')


def stages(analysis, batches, rerun):
    cases, out = {}, []
    for row in analysis['rows']:
        if not row['comparable']:
            continue
        case = cases.setdefault(row['case'], json.loads(
            (ROOT / 'eval' / 'multistage_v3' / row['case'] / 'case.json').read_text(encoding='utf-8')))
        folder = (batches['c'] if row['slot'] in rerun else batches['b']) / row['slot']
        for stage in row['grade']['stages']:
            n = stage['stage']
            own = {g['id'] for g in case['groups'] if g['since'] == n}
            out.append({'slot': row['slot'], 'case': row['case'], 'arm': row['arm'], 'stage': n,
                        'kind': 'bugfix' if case['stages'][n - 1]['bugfix'] else 'feature',
                        'resolved': own <= set(stage['new']), 'recorded_test_with_fix': stage['test_with_fix'],
                        'folder': str(folder)})
    return out, cases


def summarise(rows):
    scored = [r for r in rows if r['resolved'] and r['vacuous'] is not None]
    by_case = {}
    for r in scored:
        by_case.setdefault(r['case'], {}).setdefault(r['arm'], []).append(r['vacuous'])
    cases = {case: sum(arms['superpowers']) / len(arms['superpowers'])
             - sum(arms['elevenpowers']) / len(arms['elevenpowers'])
             for case, arms in sorted(by_case.items()) if len(arms) == 2}
    unscored = {}
    for r in rows:
        if r['resolved'] and r['vacuous'] is None:
            unscored.setdefault(r['arm'], {}).setdefault(r['reason'], 0)
            unscored[r['arm']][r['reason']] += 1
    return {'pooled': {arm: {'vacuous': sum(r['vacuous'] for r in scored if r['arm'] == arm),
                             'scored': sum(r['arm'] == arm for r in scored)} for arm in ARMS},
            'cases': cases, 'dropped': len({r['case'] for r in rows}) - len(cases),
            'better': sum(d > 0 for d in cases.values()), 'worse': sum(d < 0 for d in cases.values()),
            'tied': sum(d == 0 for d in cases.values()), 'p': exact_signed_rank(list(cases.values())),
            'unscored': unscored}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, default=Path('E:/ep-runs/multistage-v3-full-2026-10-30-b'))
    parser.add_argument('--continuation', type=Path, default=Path('E:/ep-runs/multistage-v3-full-2026-10-30-c'))
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--limit', type=int, help='first N stages only, to time the run')
    args = parser.parse_args()
    analysis = json.loads((HERE.parent / 'full-analysis.json').read_text(encoding='utf-8'))
    rerun = set(json.loads((HERE.parent / 'full-rerun-c.json').read_text(encoding='utf-8')))
    rows, cases = stages(analysis, {'b': args.batch, 'c': args.continuation}, rerun)
    rows = rows[:args.limit] if args.limit else rows
    jobs = [(Path(r['folder']), cases[r['case']], r['stage'], False) for r in rows]
    with ProcessPoolExecutor(args.workers) as pool:
        for row, result in zip(rows, pool.map(check, jobs)):
            row.update(result)
        forward = [r for r in rows if r['recorded_test_with_fix'] is not None]
        mismatched = [r['slot'] + f":{r['stage']}" for r in forward
                      if r['vacuous'] is None or (not r['vacuous']) != r['recorded_test_with_fix']]
        controls = []
        for arm in ARMS:
            for case in sorted(cases):
                first = next((r for r in rows if r['arm'] == arm and r['case'] == case
                              and r['resolved'] and r['vacuous'] is False), None)
                if first:
                    controls.append(first)
        stripped = list(pool.map(check, [(Path(r['folder']), cases[r['case']], r['stage'], True) for r in controls]))
    summary = {'all': summarise(rows), 'feature': summarise([r for r in rows if r['kind'] == 'feature']),
               'bugfix': summarise([r for r in rows if r['kind'] == 'bugfix']),
               'forward_check': {'recorded': len(forward), 'mismatched': mismatched},
               'adversarial_control': [{'slot': r['slot'], 'stage': r['stage'], **s} for r, s in zip(controls, stripped)]}
    for r in rows:
        del r['folder']
    out = HERE / ('stages.json' if not args.limit else 'timing.json')
    out.write_text(json.dumps(rows, indent=1), encoding='utf-8')
    if not args.limit:
        (HERE / 'summary.json').write_text(json.dumps(summary, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'adversarial_control'}, indent=1))
    print('control flagged', sum(s['vacuous'] is True for s in stripped), 'of', len(stripped))


if __name__ == '__main__':
    main()
