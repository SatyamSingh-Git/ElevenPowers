"""Discover: propose file pairs that carry the same rule, from the project alone.

Every pair of functions in different non-test source files is scored by the
rarity-weighted tokens they share, normalised by the square root of the product
of their own weights. A file pair takes its best function pair. Then: would the
top K proposals for the tree before a stage have contained the pair that stage
broke? Plan in README.md, written before this file.
"""
import ast
from collections import defaultdict
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
V3 = HERE.parent
ROOT = V3.parents[1]
for folder in ('convention-spike', 'dataflow'):
    sys.path.insert(0, str(V3 / folder))
sys.path.insert(0, str(ROOT))
from fresh import edits, seen_stages  # noqa: E402
from rank import sources, tokens  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402

KS = (10, 20, 50, 100)


def functions(text):
    try:
        parsed = ast.parse(text)
    except SyntaxError:
        return []
    found = []
    for node in ast.walk(parsed):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            segment = ast.get_source_segment(text, node)
            if segment:
                found.append((node.name, set(tokens(segment))))
    return found


def propose(project, limit=max(KS)):
    """The top file pairs, best first, as (score, file a, file b, function a, function b, shared rarest)."""
    files = sources(project)
    per_file = {path: functions(text) for path, text in files.items()}
    df = defaultdict(int)
    for path, text in files.items():
        for word in set(tokens(text)):
            df[word] += 1
    idf = {word: math.log(len(files) / count) for word, count in df.items()}
    rows = [(path, name, {w for w in words if idf.get(w, 0) > 0})
            for path, found in per_file.items() for name, words in found]
    weight = [sum(idf[w] for w in words) for _, _, words in rows]
    index = defaultdict(list)
    for i, (_, _, words) in enumerate(rows):
        for word in words:
            index[word].append(i)
    shared = defaultdict(float)
    for word, holders in index.items():
        for x in range(len(holders)):
            for y in range(x + 1, len(holders)):
                i, j = holders[x], holders[y]
                if rows[i][0] != rows[j][0]:
                    shared[i, j] += idf[word]
    best = {}
    for (i, j), total in shared.items():
        score = total / math.sqrt(weight[i] * weight[j]) if weight[i] and weight[j] else 0
        key = tuple(sorted((rows[i][0], rows[j][0])))
        if score > best.get(key, (0,))[0]:
            common = sorted(rows[i][2] & rows[j][2], key=lambda w: -idf[w])[:5]
            best[key] = (score, rows[i][1], rows[j][1], common)
    ordered = sorted(((s, a, b, fa, fb, c) for (a, b), (s, fa, fb, c) in best.items()), reverse=True)
    return ordered[:limit]


def covered(proposals, edited, dependent):
    """The 1-based position of the first proposed pair joining an edited file to the dependent, or None."""
    for place, (_, a, b, *_rest) in enumerate(proposals, 1):
        if {a, b} & set(edited) and dependent in (a, b) and a != b:
            return place
    return None


def main():
    seen = seen_stages()
    rows = []
    scratch = Path(tempfile.mkdtemp(prefix='ep-discover-'))
    try:
        for root in sorted((ROOT / 'eval' / 'multistage_v3').iterdir()):
            if not (root / 'case.json').exists():
                continue
            case = load(root)
            start = tree(case, 0, scratch / f"{case['id']}-0")
            at_start = propose(start)
            stages = case['stages']
            references = {}

            def changed_by(m):
                if m not in references:
                    references[m] = edits(tree(case, m - 1, scratch / f"{case['id']}-control-{m}-before"),
                                          tree(case, m, scratch / f"{case['id']}-control-{m}-after"))
                return references[m]
            for n, stage in enumerate(stages, 1):
                quiet = stage.get('quiet') or []
                if not quiet:
                    continue
                before = tree(case, n - 1, scratch / f"{case['id']}-{n - 1}-ref")
                proposals = propose(before)
                pairs = math.comb(len(sources(before)), 2)
                other = next(m for m in (n + 1, n - 1, n + 2, n - 2) if 1 <= m <= len(stages) and m != n)
                for which, item in enumerate(quiet):
                    after = tree(case, n, scratch / f"{case['id']}-{n}-quiet-{which}", 'quiet', which)
                    edited = [p for p in edits(before, after) if p != item['file']]
                    place = covered(proposals, edited, item['file'])
                    # Control: the same dependent joined to another stage's changed files, same proposals.
                    control = covered(proposals, [p for p in changed_by(other) if p != item['file']], item['file'])
                    rows.append({'case': case['id'], 'stage': n, 'dependent': item['file'], 'kind': item['kind'],
                                 'edited': edited, 'fresh': (case['id'], n) not in seen,
                                 'place': place, 'place_at_start': covered(at_start, edited, item['file']),
                                 'control': control,
                                 'random': {k: min(1, k * len(edited) / pairs) for k in KS} if pairs else {},
                                 'pair': next(([round(s, 3), a, b, fa, fb, c] for s, a, b, fa, fb, c in proposals
                                               if {a, b} & set(edited) and item['file'] in (a, b)), None)})
                    print(rows[-1]['case'], n, item['kind'], item['file'], 'place', place)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    (HERE / 'discover.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    for label, subset in (('never-read (decides)', [r for r in rows if r['fresh']]),
                          ('read stages', [r for r in rows if not r['fresh']])):
        print(f'{label}: {len(subset)} dependents')
        for key, name in (('place', 'review before each stage'), ('place_at_start', 'one review at stage 0'),
                          ('control', "control: another stage's edit")):
            hits = {k: sum(r[key] is not None and r[key] <= k for r in subset) for k in KS}
            print(f'   {name:30} {hits}')
        print(f"   {'random, expected':30} {({k: round(sum(r['random'].get(k, 0) for r in subset), 1) for k in KS})}")
        for kind in sorted({r['kind'] for r in subset}):
            sub = [r for r in subset if r['kind'] == kind]
            print(f"   {kind:9} {len(sub):3}  K=50: {sum(r['place'] is not None and r['place'] <= 50 for r in sub)}")


if __name__ == '__main__':
    main()
