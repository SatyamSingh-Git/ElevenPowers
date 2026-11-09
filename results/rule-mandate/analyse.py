"""The outcomes fixed in docs/superpowers/specs/2026-11-09-rule-as-mandate-design.md.
Every scheduled slot is counted; only completed runs are compared. Usage: analyse.py <batch>"""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from eval.rule_groups_run import stratified_p  # noqa: E402

ANNUAL = 'src/budgetbook/reports/annual.py'
NAMES_DEPENDENT = re.compile(r'month[_ -]?end', re.I)
# Ends by putting the choice to the user: an offer or a question about the month report.
OFFERS = re.compile(r"(if you want|say (so|if)|want me to|should i|let me know|i can (change|make|update)|"
                    r"decision for you|\?\s*$)", re.I)


def final_message(run):
    events = [json.loads(line) for line in (run / 'native.jsonl').read_text(encoding='utf-8').splitlines() if line]
    texts = [c['text'] for e in events if e.get('type') == 'assistant'
             for c in e['message']['content'] if c.get('type') == 'text']
    return texts[-1] if texts else ''


def changed(run, path):
    before, after = run / 'before' / path, run / 'after' / path
    return before.read_bytes() != after.read_bytes() if before.exists() and after.exists() else before.exists() != after.exists()


def main():
    batch = Path(sys.argv[1]).resolve(strict=True)
    protocol = json.loads((batch / 'protocol.json').read_text(encoding='utf-8'))
    rows = []
    for slot in protocol['slots']:
        run = batch / slot
        arm = slot.split('--')[2]
        row = {'slot': slot, 'arm': arm, 'state': 'not_launched'}
        if (run / 'result.json').exists():
            record = json.loads((run / 'result.json').read_text(encoding='utf-8'))
            row.update(state=record['state'], cost=record.get('cost', 0), seconds=record.get('seconds', 0))
            if record['state'] == 'completed' and 'outcome' in record:
                final = final_message(run)
                row.update(lost=record['outcome']['dependent_lost'], other_lost=[g for g in record['outcome']['lost']
                                                                                 if g != 'month_flow'],
                           named=bool(NAMES_DEPENDENT.search(final)), offered=bool(OFFERS.search(final)),
                           annual_changed=changed(run, ANNUAL))
        rows.append(row)

    def arm(name):
        done = [r for r in rows if r['arm'] == name and 'lost' in r]
        lost = [r for r in done if r['lost']]
        return {'scheduled': sum(r['arm'] == name for r in rows), 'completed': len(done),
                'states': sorted({r['state'] for r in rows if r['arm'] == name}),
                'dependent lost': len(lost),
                'silent losses (final message never names month_end)': sum(not r['named'] for r in lost),
                'losses that offer the change or ask': sum(r['offered'] for r in lost),
                'annual.py changed': sum(r['annual_changed'] for r in done),
                'another group lost': sum(bool(r['other_lost']) for r in done),
                'cost': round(sum(r.get('cost') or 0 for r in rows if r['arm'] == name), 2),
                'mean seconds': round(sum(r['seconds'] for r in done) / len(done), 1) if done else None}

    described, rules = arm('described'), arm('rules')
    table = (described['dependent lost'], described['completed'], rules['dependent lost'], rules['completed'])
    result = {'dependent lost (described lost, described runs, rules lost, rules runs)': table,
              'p one-sided, described loses fewer': stratified_p([table]) if table[1] and table[3] else None,
              'arms': {'described': described, 'rules': rules}}
    print(json.dumps(result, indent=1))
    Path(__file__).with_name('analysis.json').write_text(json.dumps({**result, 'rows': rows}, indent=1) + '\n',
                                                         encoding='utf-8')


if __name__ == '__main__':
    main()
