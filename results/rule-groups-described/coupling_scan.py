"""On each covered v3 stage: does the reference change the functions the certifying proposal named, or does the
stage break another tie between the same files (as parcelpost 5 does)? $0.

Usage: coupling_scan.py <new scratch dir>. Writes coupling-scan.json next to this file."""
import ast
import difflib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.milestones.propose import propose  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402
from eval.rule_groups_run import certify  # noqa: E402


def functions(text):
    """(name, first line, last line) for every function and method."""
    try:
        nodes = ast.walk(ast.parse(text))
    except SyntaxError:
        return []
    return [(n.name, n.lineno, n.end_lineno) for n in nodes if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def changed_functions(before, after):
    old, new = before.splitlines(), after.splitlines()
    lines_old, lines_new = set(), set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag != 'equal':
            lines_old.update(range(i1 + 1, max(i2, i1 + 1) + 1))
            lines_new.update(range(j1 + 1, max(j2, j1 + 1) + 1))
    names = {name for name, a, b in functions(before) if lines_old & set(range(a, b + 1))}
    return names | {name for name, a, b in functions(after) if lines_new & set(range(a, b + 1))}


def main():
    scratch = Path(sys.argv[1]).resolve()
    scan = json.loads((ROOT / 'results' / 'rule-groups-harm' / 'stage-scan.json').read_text(encoding='utf-8'))
    rows = []
    for name in sorted({r['case'] for r in scan if r['kind'] == 'covered'}):
        case = load(ROOT / 'eval' / 'multistage_v3' / name)
        certified = {e['id'] for e in certify(case, scratch / name / 'certify')}
        start = tree(case, 0, scratch / name / 'start')
        subprocess.run(['git', 'init', '-q'], cwd=start, check=True)
        subprocess.run(['git', 'add', '-A'], cwd=start, check=True, capture_output=True)
        proposals = [p for p in propose(start, limit=50)['proposals'] if p['entry']['id'] in certified]
        for n in sorted(r['stage'] for r in scan if r['case'] == name and r['kind'] == 'covered'):
            before = tree(case, n - 1, scratch / name / f'{n}-before')
            after = tree(case, n, scratch / name / f'{n}-after')
            for quiet in case['stages'][n - 1]['quiet']:
                dependent = quiet['file']
                for p in proposals:
                    if dependent not in p['files']:
                        continue
                    touched = {}
                    for path in p['files']:
                        a = (before / path).read_text(encoding='utf-8') if (before / path).exists() else ''
                        b = (after / path).read_text(encoding='utf-8') if (after / path).exists() else ''
                        touched[path] = sorted(changed_functions(a, b))
                    other = next(f for f in p['files'] if f != dependent)
                    if not touched[other]:
                        continue  # this proposal's other file is not changed at this stage; it does not cover the pair
                    named = dict(zip(p['files'], p['functions']))
                    rows.append({'stage': f'{name} {n}', 'dependent': dependent, 'rule': p['entry']['id'],
                                 'proposed': named, 'changed': touched,
                                 'rule_changed': any(named[f] in touched[f] for f in p['files'])})
                    print(json.dumps({k: rows[-1][k] for k in ('stage', 'rule', 'rule_changed')}), flush=True)
    Path(__file__).with_name('coupling-scan.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    stages = {}
    for r in rows:
        stages[r['stage']] = stages.get(r['stage'], False) or r['rule_changed']
    print(f"covered stages: {len(stages)}; the stage changes a proposed function in {sum(stages.values())}; "
          f"another tie between the same files in {len(stages) - sum(stages.values())}: "
          f"{sorted(s for s, v in stages.items() if not v)}")


if __name__ == '__main__':
    main()
