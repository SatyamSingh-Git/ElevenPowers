"""The outcomes fixed in docs/superpowers/specs/2026-11-09-declared-rule-gate-design.md, from the two
sealed batches. Every scheduled slot is counted; only completed runs are compared.
Usage: analyse.py <primary batch> <harm batch>"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from eval.rule_groups_run import collect, stratified_p  # noqa: E402

RULE = 'rule-summarise-_spent_by_category'
OTHER_FILE = 'src/budgetbook/reports/annual.py'


def enrich(batch, rows):
    for row in rows:
        folder = Path(batch) / row['slot']
        ledger_path = folder / 'after' / '.elevenpowers' / 'ledger.json'
        if not ledger_path.exists():
            ledger_path = folder / 'work' / '.elevenpowers' / 'ledger.json'
        ledger = json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else {}
        decisions = ledger.get('decisions', [])
        row['rules_sent'] = ledger.get('rules_sent', [])
        row['rule_blocks'] = sum(d['what'] == 'gate blocked' and 'rules left behind' in d['why'] for d in decisions)
        row['blocks'] = sum(d['what'] == 'gate blocked' for d in decisions)
        row['released'] = [d['why'] for d in decisions if d['what'] == 'rule gate released']
        row['touched'] = ledger.get('touched', [])
    return rows


def arm_summary(rows, arm):
    done = [r for r in rows if r['arm'] == arm and r['comparable']]
    return {'scheduled': sum(r['arm'] == arm for r in rows), 'completed': len(done),
            'states': sorted({r['state'] for r in rows if r['arm'] == arm}),
            'cost': round(sum(r.get('cost') or 0 for r in rows if r['arm'] == arm), 2),
            'mean_seconds': round(sum(r['seconds'] for r in done) / len(done), 1) if done else None,
            'any_group_lost': sum(bool(r['lost']) for r in done),
            'rule_blocked': sum(r['rule_blocks'] > 0 for r in done),
            'released': sum(bool(r['released']) for r in done)}


def lost_any(rows, arm, name, stage):
    done = [r for r in rows if (r['arm'], r['case'], r['stage']) == (arm, name, stage) and r['comparable']]
    return sum(bool(r['lost']) for r in done), len(done)


def main():
    primary_batch, harm_batch = sys.argv[1:3]
    primary = collect(primary_batch)
    rows = enrich(primary_batch, primary['rows'])
    done = [r for r in rows if r['comparable']]
    table = [(sum(r['dependent_lost'] for r in done if r['arm'] == 'gate'), sum(r['arm'] == 'gate' for r in done),
              sum(r['dependent_lost'] for r in done if r['arm'] == 'note'), sum(r['arm'] == 'note' for r in done))]
    sent = [r for r in done if r['arm'] == 'gate' and any(RULE in s for s in r['rules_sent'])]
    kept_gate = [r for r in done if r['arm'] == 'gate' and not r['dependent_lost']]
    result = {
        'primary': {
            'dependent lost (gate lost, gate runs, note lost, note runs)': table[0],
            'p one-sided, gate loses fewer': stratified_p(table) if table[0][1] and table[0][3] else None,
            'arms': {arm: arm_summary(rows, arm) for arm in ('note', 'gate')},
        },
        'conversion': {'gate runs sent back for the dependent rule': len(sent),
                       'of those, dependent kept': sum(not r['dependent_lost'] for r in sent)},
        'harm on the primary stage': {
            'gate runs that kept the dependent': len(kept_gate),
            'of those, another group lost': sum(bool(set(r['lost'])) for r in kept_gate),
            f'of those, {OTHER_FILE} changed': sum(OTHER_FILE in r['touched'] for r in kept_gate),
            f'note runs with {OTHER_FILE} changed': sum(OTHER_FILE in r['touched'] for r in done
                                                       if r['arm'] == 'note'),
        },
    }
    harm = collect(harm_batch)
    harm_rows = enrich(harm_batch, harm['rows'])
    stages = [tuple(s) for s in json.loads((Path(harm_batch) / 'protocol.json').read_text(encoding='utf-8'))['stages']]
    # Swapped so the test asks whether `gate` loses MORE: note's losses play the role of the arm that loses fewer.
    tables = [(*lost_any(harm_rows, 'note', *s), *lost_any(harm_rows, 'gate', *s)) for s in stages]
    usable = [t for t in tables if t[1] and t[3]]
    result['harm stages'] = {
        'any group lost by stage (note lost, note runs, gate lost, gate runs)':
            {f'{n} {s}': t for (n, s), t in zip(stages, tables)},
        'p one-sided, gate loses more': stratified_p(usable) if usable else None,
        'arms': {arm: arm_summary(harm_rows, arm) for arm in ('note', 'gate')},
    }
    result['released replies'] = {r['slot']: r['released'] for r in rows + harm_rows if r['released']}
    print(json.dumps(result, indent=1))
    out = Path(__file__).with_name('analysis.json')
    out.write_text(json.dumps({**result, 'rows': {'primary': rows, 'harm': harm_rows}}, indent=1) + '\n',
                   encoding='utf-8')


if __name__ == '__main__':
    main()
