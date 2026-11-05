"""Where the 51 never-read dependents' rules sit: inside a function, or outside any.

For each dependent, the lines its fix changes and the lines the stage's other edits change,
from the tree before the stage to the reference after it, each placed by the AST of its side.
Writes where.json next to this file and prints a summary."""
import ast
import difflib
import json
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from eval.multistage_cases import load, tree  # noqa: E402


def sites(source, lines):
    nodes = [n for n in ast.walk(ast.parse(source)) if hasattr(n, 'end_lineno')]
    text = source.splitlines()
    found = set()
    for line in lines:
        if not text[line - 1].strip() or text[line - 1].strip().startswith('#'):
            continue
        holders = [n for n in nodes if n.lineno <= line <= n.end_lineno]
        if any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in holders):
            found.add('import')
        elif any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in holders):
            found.add('function')
        elif any(isinstance(n, ast.ClassDef) for n in holders):
            found.add('class')
        else:
            found.add('module')
    return found


def changed(before, after):
    a, b = before.splitlines(), after.splitlines()
    old, new = set(), set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != 'equal':
            old.update(range(i1 + 1, i2 + 1))
            new.update(range(j1 + 1, j2 + 1))
    return sites(before, old) | sites(after, new)


def main():
    rows = [r for r in json.loads((ROOT / 'results/multistage-v3/discover/discover.json').read_text(encoding='utf-8'))
            if r['fresh']]
    scratch = Path(tempfile.mkdtemp(prefix='ep-where-'))
    trees, out = {}, []

    def text(case, stage, path):
        if (case['id'], stage) not in trees:
            trees[case['id'], stage] = tree(case, stage, scratch / f"{case['id']}-{stage}")
        file = trees[case['id'], stage] / path
        return file.read_text(encoding='utf-8') if file.exists() else ''
    try:
        for r in rows:
            case, n = load(ROOT / 'eval/multistage_v3' / r['case']), r['stage']
            edited = set()
            for path in r['edited']:
                if path.endswith('.py'):
                    edited |= changed(text(case, n - 1, path), text(case, n, path))
            out.append({'case': r['case'], 'stage': n, 'kind': r['kind'], 'dependent_file': r['dependent'],
                        'place': r['place'], 'covered': r['place'] is not None and r['place'] <= 50,
                        'dependent': sorted(changed(text(case, n - 1, r['dependent']), text(case, n, r['dependent']))),
                        'edited': sorted(edited)})
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    (HERE / 'where.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
    for covered in (True, False):
        sub = [o for o in out if o['covered'] == covered]
        outside = [o for o in sub if 'function' not in o['dependent'] or 'function' not in o['edited']]
        print('covered' if covered else 'missed', len(sub), '| a side with no changed line in a function:',
              len(outside), '(dependent', sum('function' not in o['dependent'] for o in outside),
              ', edit', sum('function' not in o['edited'] for o in outside), ')')
        for o in outside:
            print('   ', o['kind'], o['case'], o['stage'], o['dependent_file'], 'dependent', o['dependent'],
                  'edit', o['edited'])


if __name__ == '__main__':
    main()
