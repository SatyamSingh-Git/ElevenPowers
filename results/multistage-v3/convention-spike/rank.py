"""Spike ($0): would rare tokens shared with the edited functions point at the left-behind dependent?

For each of the ElevenPowers arm's 31 losses, take the functions the agent's
edit touched (before and after the stage), collect their identifiers, attribute
names, string literals and numbers, weight each by its rarity across the
project's source files (IDF), and rank every other non-test source file by the
weight of the tokens it shares. The question is the dependent's rank. The
import-graph brief this replaces found 4 of 31. Borrowed: the token weighting
behind clone and plagiarism detectors; nothing here is product code.
"""
import ast
import difflib
import io
import json
import math
from pathlib import Path
import sys
import tokenize

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from core.surface import TEST_NAME  # noqa: E402

V3 = ROOT / 'results' / 'multistage-v3'
BATCHES = {'b': Path('E:/ep-runs/multistage-v3-full-2026-10-30-b'), 'c': Path('E:/ep-runs/multistage-v3-full-2026-10-30-c')}
KEYWORDS = set(__import__('keyword').kwlist) | {'self', 'cls', 'None', 'True', 'False', 'int', 'str', 'float', 'len',
                                                 'dict', 'list', 'return', 'value', 'name', 'path', 'row', 'rows'}


def tokens(source):
    found = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type in (tokenize.NAME, tokenize.STRING, tokenize.NUMBER) and token.string not in KEYWORDS:
                found.append(token.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return found


def functions_touching(source, lines):
    """The source of every function or class whose span holds a changed line; the lines themselves otherwise."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ''
    text = source.splitlines()
    spans = [(n.lineno, n.end_lineno) for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(n.lineno <= l <= n.end_lineno for l in lines)]
    if not spans:
        return '\n'.join(text[l - 1] for l in lines if 0 < l <= len(text))
    return '\n'.join('\n'.join(text[a - 1:b]) for a, b in spans)


def changed(before, after):
    """Changed line numbers on each side."""
    old, new = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, before.splitlines(), after.splitlines()).get_opcodes():
        if tag != 'equal':
            old += range(i1 + 1, max(i2, i1 + 1) + 1)
            new += range(j1 + 1, max(j2, j1 + 1) + 1)
    return old, new


def sources(tree):
    return {p.relative_to(tree).as_posix(): p.read_text(encoding='utf-8', errors='replace')
            for p in tree.rglob('*.py') if not TEST_NAME.search(p.relative_to(tree).as_posix())}


def rank(before_tree, after_tree, edited, dependent):
    before, after = sources(before_tree), sources(after_tree)
    query = []
    for path in edited:
        if path not in before or TEST_NAME.search(path):
            continue
        old, new = changed(before[path], after.get(path, ''))
        query += tokens(functions_touching(before[path], old)) + tokens(functions_touching(after.get(path, ''), new))
    documents = {path: set(tokens(text)) for path, text in before.items()}
    idf = {}
    for words in documents.values():
        for word in words:
            idf[word] = idf.get(word, 0) + 1
    idf = {word: math.log(len(documents) / count) for word, count in idf.items()}
    query = set(query)
    scores = sorted(((sum(idf.get(w, 0) for w in query & words), path) for path, words in documents.items()
                     if path not in edited), reverse=True)
    order = [path for _, path in scores]
    shared = sorted(query & documents.get(dependent, set()), key=lambda w: -idf.get(w, 0))[:6]
    return (order.index(dependent) + 1 if dependent in order else None), len(order), shared


def main():
    diagnosis = json.loads((V3 / 'diagnosis-elevenpowers-losses.json').read_text(encoding='utf-8'))
    rerun = set(json.loads((V3 / 'full-rerun-c.json').read_text(encoding='utf-8')))
    rows = []
    for loss in diagnosis:
        folder = BATCHES['c' if loss['slot'] in rerun else 'b'] / loss['slot'] / 'snapshots'
        n = loss['stage']
        for dependent in loss['dependent']:
            place, of, shared = rank(folder / str(n - 1), folder / str(n), loss['agent_edited'], dependent)
            rows.append({'slot': loss['slot'], 'stage': n, 'dependent': dependent, 'rank': place, 'of': of,
                         'shared_rarest': shared, 'import_brief': loss['verdict'] != 'not detected'})
            print(f"{loss['slot']:32} s{n} rank {place}/{of}  {dependent}  {shared}")
    # Adversarial control: the same dependent, ranked against the edit of another stage of the
    # same conversation. If it still ranks high, it is a central file, not something this edit points at.
    for row in rows:
        folder = BATCHES['c' if row['slot'] in rerun else 'b'] / row['slot'] / 'snapshots'
        other = row['stage'] + 1 if (folder / str(row['stage'] + 1)).exists() else row['stage'] - 1
        before, after = folder / str(other - 1), folder / str(other)
        edited = [p for p in sources(after) if p not in sources(before) or sources(after)[p] != sources(before)[p]]
        row['control_rank'], _, _ = rank(before, after, edited, row['dependent'])
        row['control_stage'] = other
    (Path(__file__).with_name('ranks.json')).write_text(json.dumps(rows, indent=1), encoding='utf-8')
    for k in (1, 3, 5):
        print(f'top {k}:', sum(r['rank'] is not None and r['rank'] <= k for r in rows), 'of', len(rows),
              '| control, another stage\'s edit:', sum(r['control_rank'] is not None and r['control_rank'] <= k
                                                      for r in rows))
    print('expected at random, top 3:', round(sum(3 / r['of'] for r in rows), 1))


if __name__ == '__main__':
    main()
