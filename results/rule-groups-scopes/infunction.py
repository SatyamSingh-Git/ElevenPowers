"""The 17 missed never-read dependents whose rule sits in functions on both sides: do the changed
functions share any rare word at all, and how far below the 50th proposal does their pair score?"""
import ast
import difflib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from core.evidence import scan_sources  # noqa: E402
from core.milestones.propose import _tokens, propose  # noqa: E402
from core.surface import TEST_NAME  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402

where = json.loads((ROOT / 'results/rule-groups-scopes/where.json').read_text(encoding='utf-8'))
rows = [w for w in where if not w['covered'] and 'function' in w['dependent'] and 'function' in w['edited']]
discover = {(r['case'], r['stage'], r['dependent']): r for r in
            json.loads((ROOT / 'results/multistage-v3/discover/discover.json').read_text(encoding='utf-8'))}


def old_lines(before, after):
    a, b = before.splitlines(), after.splitlines()
    lines = set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ('replace', 'delete'):
            lines.update(range(i1 + 1, i2 + 1))
        elif tag == 'insert':
            lines.update({i1, i1 + 1})
    return lines


def functions(source):
    text = source.splitlines()
    return [(n.name, n.lineno, n.end_lineno, _tokens('\n'.join(text[n.lineno - 1:n.end_lineno])))
            for n in ast.walk(ast.parse(source)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


scratch = Path(tempfile.mkdtemp(prefix='ep-infunction-'))
out = []
try:
    for w in rows:
        case, n = load(ROOT / 'eval/multistage_v3' / w['case']), w['stage']
        before = tree(case, n - 1, scratch / f"{w['case']}-{n}-before")
        after = tree(case, n, scratch / f"{w['case']}-{n}-after")
        subprocess.run(['git', 'init', '-q'], cwd=before, check=True)
        subprocess.run(['git', 'add', '-A'], cwd=before, check=True, capture_output=True)
        files = [p for p in scan_sources(before).files if p.endswith('.py') and not TEST_NAME.search(p)]
        held = {}
        for p in files:
            for word in _tokens((before / p).read_text(encoding='utf-8')):
                held[word] = held.get(word, 0) + 1
        idf = {word: math.log(len(files) / count) for word, count in held.items()}

        def touched(path):
            src = (before / path).read_text(encoding='utf-8')
            dst = (after / path).read_text(encoding='utf-8') if (after / path).exists() else ''
            lines = old_lines(src, dst)
            return [(name, {t for t in words if idf.get(t, 0) > 0}) for name, start, end, words in functions(src)
                    if any(start <= line <= end for line in lines)]
        dependent = touched(w['dependent_file'])
        record = discover[w['case'], n, w['dependent_file']]
        edits = [(path, f) for path in record['edited'] if path.endswith('.py') for f in touched(path)]
        pairs = []
        for path, (en, ew) in edits:
            for dn, dw in dependent:
                weight = math.sqrt(math.fsum(idf[t] for t in ew) * math.fsum(idf[t] for t in dw)) or 1
                common = ew & dw
                pairs.append((math.fsum(idf[t] for t in common) / weight, path, en, dn,
                              sorted(common, key=lambda t: -idf[t])[:6]))
        pairs.sort(reverse=True)
        listed = propose(before, limit=100, seconds=120)['proposals']
        bar = listed[49]['score'] if len(listed) >= 50 else None
        best = pairs[0] if pairs else None
        out.append({'case': w['case'], 'stage': n, 'kind': w['kind'], 'dependent': w['dependent_file'],
                    'place': w['place'], 'score_50th': bar, 'changed_pairs': len(pairs),
                    'sharing_any_rare_word': sum(bool(p[4]) for p in pairs),
                    'best': best and {'score': round(best[0], 4), 'edit': f'{best[1]}:{best[2]}', 'dependent_function': best[3],
                                      'shared': best[4]}})
        print(json.dumps(out[-1]), flush=True)
finally:
    shutil.rmtree(scratch, ignore_errors=True)
(HERE / 'infunction.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
none = [o for o in out if not o['sharing_any_rare_word']]
print(f'{len(out)} rows; changed functions share no rare word in {len(none)}; '
      f'share some but score below the 50th in {len(out) - len(none)}')
