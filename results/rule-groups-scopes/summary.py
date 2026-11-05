"""Compare measure-before.json with measure-after.json by the rules README.md set before either ran."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KS = (10, 20, 50, 100)


def within(rows, key, k):
    return sum(r[key] is not None and r[key] <= k for r in rows)


def body(functions):
    return any(name == '<module>' or name.startswith('class ') for name in functions)


def main():
    before, after = (json.loads((HERE / f'measure-{label}.json').read_text(encoding='utf-8')) for label in ('before', 'after'))
    lines, verdict = [], {}
    for fresh, title in ((True, '51 never-read dependents'), (False, '17 read stages, for completeness')):
        lines.append(f'{title}, covered within K = {KS}:')
        for label, report in (('before', before), ('after', after)):
            rows = [r for r in report['v3'] if r['fresh'] == fresh]
            lines.append(f"  {label:6} {len(rows)} rows | proposals {[within(rows, 'place', k) for k in KS]}"
                         f" | control {[within(rows, 'control', k) for k in KS]}")
            if fresh:
                verdict[label] = (within(rows, 'place', 50), within(rows, 'place', 50) - within(rows, 'control', 50))
    keyed = {(r['case'], r['stage'], r['dependent']): r for r in before['v3']}
    for r in after['v3']:
        was = keyed[r['case'], r['stage'], r['dependent']]
        old, new = (x is not None and x <= 50 for x in (was['place'], r['place']))
        if old != new or was['place'] != r['place']:
            lines.append(f"  {'ENTERS' if new and not old else 'LEAVES' if old and not new else 'moves '} top 50: "
                         f"{'read ' if not r['fresh'] else ''}{r['kind']} {r['case']} {r['stage']} {r['dependent']}"
                         f" place {was['place']} -> {r['place']}")
    lines.append('Real projects (time budget: the propose deadline, 30 s):')
    budget = True
    for name, row in after['real'].items():
        old = before['real'][name]
        issues = (row['coverage'] or {}).get('issues', [])
        timed_out = any('time budget' in i for i in issues)
        budget &= row['exit'] == 0 and not timed_out
        pairs = [p for p in row['top50'] if body(p[1])]
        lines.append(f"  {name}: exit {row['exit']}, {old['seconds']} s -> {row['seconds']} s, time budget reached "
                     f"{timed_out}, bodies {(row['coverage'] or {}).get('bodies')}, top 50 with a body {len(pairs)}"
                     f" of {len(row['top50'])}")
        lines += [f"     {p[0][0]} ({p[1][0]}) <-> {p[0][1]} ({p[1][1]}): {', '.join(p[2])}" for p in pairs[:5]]
    lines.append("Reviewed run's accepted pairs at stage 0:")
    accepted = json.loads((ROOT / 'results/rule-groups-acted-on-reviewed/accepted.json').read_text(encoding='utf-8'))
    for case, ids in accepted.items():
        old, new = before['stage0'][case], after['stage0'][case]
        same = [i for i in ids if new.get(i) == old[i]]
        moved = [i for i in ids if i not in same and old[i] in new.values()]
        lines.append(f'  {case}: {len(same)} of {len(ids)} same id and files; {len(moved)} same files under another id;'
                     f' lost {[i for i in ids if i not in same and i not in moved]}')
    adopted = verdict['after'][0] >= 23 and verdict['after'][1] >= verdict['before'][1] and budget
    lines.append(f"Decided in advance: covered at K = 50 {verdict['before'][0]} -> {verdict['after'][0]} (bar 23); margin "
                 f"over control {verdict['before'][1]} -> {verdict['after'][1]} (bar: no smaller); real projects within "
                 f"budget {budget}. Adopted: {adopted}")
    text = '\n'.join(lines) + '\n'
    (HERE / 'summary.txt').write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
