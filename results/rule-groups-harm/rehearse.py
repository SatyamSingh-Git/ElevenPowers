"""Gate 1 of the harm design, at $0, on every stage it runs: the declarations load and only the rules arm
has them; the reference regresses nothing (the dependent excepted) and does the request; the untouched
tree does not do the request. Usage: rehearse.py <new scratch dir>."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.milestones.definition import load as declarations  # noqa: E402
from eval import multistage_oracles as oracles  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402
from eval.rule_groups_run import certify, outcome, workspace  # noqa: E402

PRIMARY = {('household_budget', 7), ('recipe_box', 4), ('library_loans', 1), ('payroll_lite', 2), ('parcelpost', 5)}


def stages():
    scan = json.loads(Path(__file__).with_name('stage-scan.json').read_text(encoding='utf-8'))
    return [(r['case'], r['stage'], r['kind']) for r in scan
            if r['kind'] == 'self-contained' or (r['kind'] == 'covered' and (r['case'], r['stage']) not in PRIMARY)]


def main():
    scratch = Path(sys.argv[1]).resolve()
    rows, cases = [], {}
    for name, n, kind in stages():
        if name not in cases:
            case = load(ROOT / 'eval' / 'multistage_v3' / name)
            entries = certify(case, scratch / name / 'certify')
            control = workspace(case, 1, 'control', scratch / name / 'control', entries)
            rules = workspace(case, 1, 'rules', scratch / name / 'rules', entries)
            loaded = declarations(rules)
            cases[name] = (case, not loaded['issues'] and len(loaded['milestones']) == len(entries) > 0
                           and not (control / 'elevenpowers.milestones.json').exists())
        case, declared_ok = cases[name]
        stage = case['stages'][n - 1]
        fails = {g for quiet in stage.get('quiet') or [] for g in quiet.get('fails', [])}
        own = [g['id'] for g in case['groups'] if g['since'] == n]
        before = tree(case, n - 1, scratch / name / f'{n}-before')
        reference = tree(case, n, scratch / name / f'{n}-reference')
        graded = outcome(case, n, before, reference)
        untouched = oracles.groups(case, n, before)
        row = {'stage': f'{name} {n}', 'kind': kind, 'declarations ok': declared_ok,
               'reference regresses': sorted(set(graded['lost']) - fails),
               'reference does request': bool(own) and all(graded['groups'].get(g) == 'passed' for g in own),
               'untouched does request': bool(own) and all(untouched.get(g) == 'passed' for g in own)}
        row['passes'] = (row['declarations ok'] and not row['reference regresses'] and row['reference does request'])
        rows.append(row)
        print(json.dumps(row), flush=True)
    Path(__file__).with_name('rehearsal.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    informative = sum(not r['untouched does request'] for r in rows)
    print('gate 1:', 'PASS' if all(r['passes'] for r in rows) else 'FAIL', f"({sum(r['passes'] for r in rows)} of {len(rows)});",
          f'request-done informative on {informative} of {len(rows)}')


if __name__ == '__main__':
    main()
