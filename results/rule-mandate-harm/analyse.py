"""The outcomes fixed in docs/superpowers/specs/2026-11-10-rule-as-mandate-harm-design.md.
Every scheduled slot is counted; only completed runs are compared. Usage: analyse.py <batch> <scratch dir>"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from eval.multistage_cases import load, tree  # noqa: E402
from eval.rule_groups_run import stratified_p  # noqa: E402


def sources(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in Path(root).rglob('*.py')
            if '.venv' not in p.parts and '.elevenpowers' not in p.parts}


def changed(before, after):
    old, new = sources(before), sources(after)
    return {path for path in old.keys() | new.keys() if old.get(path) != new.get(path)}


def main():
    batch, scratch = Path(sys.argv[1]).resolve(strict=True), Path(sys.argv[2]).resolve()
    protocol = json.loads((batch / 'protocol.json').read_text(encoding='utf-8'))
    rules = protocol['rules']
    needless_files = {}
    for name, stage in protocol['stages']:
        case = load(Path(protocol['cases_root']) / name)
        reference = changed(tree(case, stage - 1, scratch / f'{name}-{stage}-before'),
                            tree(case, stage, scratch / f'{name}-{stage}-after'))
        behind = [e for e in rules[name] if set(e['inputs']) & reference and set(e['inputs']) - reference]
        needless_files[f'{name}--{stage}'] = sorted({p for e in behind for p in e['inputs']} - reference)
    rows = []
    for slot in protocol['slots']:
        name, stage, arm, _ = slot.split('--')
        row = {'slot': slot, 'stage': f'{name}--{stage}', 'arm': arm, 'state': 'not_launched'}
        run = batch / slot
        if (run / 'result.json').exists():
            record = json.loads((run / 'result.json').read_text(encoding='utf-8'))
            row.update(state=record['state'], cost=record.get('cost', 0), seconds=record.get('seconds', 0))
            if record['state'] == 'completed' and 'outcome' in record:
                edits = changed(run / 'before', run / 'after')
                row.update(lost=record['outcome']['lost'], dependent_lost=record['outcome']['dependent_lost'],
                           needless=sorted(edits & set(needless_files[row['stage']])))
        rows.append(row)

    def lost(arm, stage):
        done = [r for r in rows if (r['arm'], r['stage']) == (arm, stage) and 'lost' in r]
        return sum(bool(r['lost']) for r in done), len(done)

    stages = [f'{n}--{s}' for n, s in protocol['stages']]
    # `rules` first: the test asks whether `rules` loses fewer, which is `described` losing more.
    tables = [(*lost('rules', s), *lost('described', s)) for s in stages]
    usable = [t for t in tables if t[1] and t[3]]

    def arm(name):
        done = [r for r in rows if r['arm'] == name and 'lost' in r]
        return {'scheduled': sum(r['arm'] == name for r in rows), 'completed': len(done),
                'states': sorted({r['state'] for r in rows if r['arm'] == name}),
                'any group lost': sum(bool(r['lost']) for r in done),
                'dependent lost': sum(bool(r['dependent_lost']) for r in done),
                'runs with a needless edit': sum(bool(r['needless']) for r in done),
                'needless edits (files)': sum(len(r['needless']) for r in done),
                'cost': round(sum(r.get('cost') or 0 for r in rows if r['arm'] == name), 2),
                'mean seconds': round(sum(r['seconds'] for r in done) / len(done), 1) if done else None}

    result = {'p one-sided, described loses more': stratified_p(usable) if usable else None,
              'stages compared': len(usable),
              'arms': {'rules': arm('rules'), 'described': arm('described')},
              'stages with a needless-edit target': sum(bool(v) for v in needless_files.values())}
    print(json.dumps(result, indent=1))
    Path(__file__).with_name('analysis.json').write_text(
        json.dumps({**result, 'needless_files': needless_files, 'rows': rows}, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
