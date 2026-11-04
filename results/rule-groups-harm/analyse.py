"""The harm run's report, as pre-registered: regressions other than the declared dependent (primary), edits
to declared files beyond the reference, the dependent on covered stages, request done, cost and delivery.

Usage: analyse.py <batch>. Writes analysis-<batch name>.json next to this file and prints a summary."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from eval.multistage_cases import load  # noqa: E402
from eval.rule_groups_run import ARMS, collect, stratified_p  # noqa: E402


def changed(folder, path):
    before, after = folder / 'before' / path, folder / 'after' / path
    return before.exists() != after.exists() or (before.exists() and before.read_bytes() != after.read_bytes())


def main():
    batch = Path(sys.argv[1]).resolve(strict=True)
    protocol = json.loads((batch / 'protocol.json').read_text(encoding='utf-8'))
    scan = {(r['case'], r['stage']): r for r in json.loads(Path(__file__).with_name('stage-scan.json').read_text(encoding='utf-8'))}
    value = collect(batch)
    cases = {}
    for row in value['rows']:
        case = cases.setdefault(row['case'], load(ROOT / 'eval' / 'multistage_v3' / row['case']))
        stage = case['stages'][row['stage'] - 1]
        fails = {g for quiet in stage.get('quiet') or [] for g in quiet.get('fails', [])}
        own = [g['id'] for g in case['groups'] if g['since'] == row['stage']]
        folder = batch / row['slot']
        record = json.loads((folder / 'result.json').read_text(encoding='utf-8')) if (folder / 'result.json').exists() else {}
        groups = record.get('outcome', {}).get('groups', {})
        inputs = sorted({p for e in protocol['rules'][row['case']] for p in e['inputs']})
        info = scan[(row['case'], row['stage'])]
        row.update(kind=info['kind'], regressed=bool(set(row.get('lost') or []) - fails),
                   request_done=bool(own) and all(groups.get(g) == 'passed' for g in own) if groups else None,
                   beyond_reference_eligible=info['kind'] == 'self-contained' and not info['reference_touches_declared'],
                   declared_changed=[p for p in inputs if changed(folder, p)] if (folder / 'after').exists() else [])

    def tables(rows_of, measure):
        out = []
        for name, stage in protocol['stages']:
            cell = {arm: [r for r in rows_of if (r['case'], r['stage'], r['arm']) == (name, stage, arm) and r['comparable']]
                    for arm in ARMS}
            if cell['rules'] and cell['control']:
                # Arms swapped: the runner's test asks whether the first arm loses fewer.
                out.append((sum(map(measure, cell['control'])), len(cell['control']),
                            sum(map(measure, cell['rules'])), len(cell['rules'])))
        return out

    rows = value['rows']
    eligible = [r for r in rows if r['beyond_reference_eligible']]
    covered = [r for r in rows if r['kind'] == 'covered']
    report = {'states': {}, 'primary_harm_p': None, 'beyond_reference_p': None, 'arms': {}}
    for r in rows:
        report['states'][r['state']] = report['states'].get(r['state'], 0) + 1
    regress = tables(rows, lambda r: r['regressed'])
    report['primary_harm_p'] = stratified_p(regress) if regress else None
    beyond = tables(eligible, lambda r: bool(r['declared_changed']))
    report['beyond_reference_p'] = stratified_p(beyond) if beyond else None
    for arm in ARMS:
        mine = [r for r in rows if r['arm'] == arm and r['comparable']]
        report['arms'][arm] = {
            'comparable': len(mine),
            'regressed': sum(r['regressed'] for r in mine),
            'declared_changed_beyond_reference': sum(bool(r['declared_changed']) for r in mine if r['beyond_reference_eligible']),
            'beyond_reference_eligible': sum(r['beyond_reference_eligible'] for r in mine),
            'covered_dependent_lost': sum(bool(r['dependent_lost']) for r in mine if r['kind'] == 'covered'),
            'covered': sum(r['kind'] == 'covered' for r in mine),
            'request_done': sum(bool(r['request_done']) for r in mine),
            'cost': round(sum(r.get('cost') or 0 for r in rows if r['arm'] == arm), 2),
            'mean_seconds': round(sum(r['seconds'] for r in mine) / len(mine), 1) if mine else None,
            'briefed': sum(bool(r.get('declared_files_briefed')) for r in mine)}
    covered_tables = [(r_lost, r_n, c_lost, c_n) for c_lost, c_n, r_lost, r_n in tables(covered, lambda r: bool(r['dependent_lost']))]
    report['covered_dependent_p_fewer'] = stratified_p(covered_tables) if covered_tables else None
    report['rows'] = rows
    Path(__file__).with_name(f'analysis-{batch.name}.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    print('states', report['states'])
    print('primary: regressions other than the dependent, one-sided p for harm:', report['primary_harm_p'])
    print('declared files changed beyond the reference, one-sided p for more:', report['beyond_reference_p'])
    print('covered stages, dependent lost, one-sided p for fewer:', report['covered_dependent_p_fewer'])
    for arm, summary in report['arms'].items():
        print(arm, summary)


if __name__ == '__main__':
    main()
