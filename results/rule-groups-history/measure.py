"""Coverage of the 160 quiet dependents in benchmark.json, from each commit's parent tree: the product's
proposals, co-change over the 1,000 commits before it, their controls and the two combined.
Run: python measure.py <folder holding the four clones>"""
from collections import Counter, defaultdict
from itertools import combinations
import io
import json
from math import comb
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from build import PROJECTS, commits, git, source  # noqa: E402
from core.atlas import source_model  # noqa: E402
from core.milestones.propose import propose  # noqa: E402

KS = (10, 20, 50, 100)
WINDOW, LARGEST = 1000, 20


def place(pairs, dependent, edit):
    edit = set(edit)
    return next((i for i, pair in enumerate(pairs, 1) if dependent in pair and pair & edit), None)


def co_change(repo, parent, present, modified):
    counts = Counter()
    used = 0
    for sha in git(repo, 'rev-list', '--no-merges', f'--max-count={WINDOW}', parent).split():
        files = [p for p in modified.get(sha, []) if p in present]
        if 2 <= len(modified.get(sha, [])) <= LARGEST:
            used += 1
            counts.update(combinations(sorted(files), 2))
    return [set(pair) for pair, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))], used


def sign_test(rows, a, b, k):
    """One-sided exact sign test that a covers more than b within k, on the discordant rows."""
    wins = sum(within(r[a], k) and not within(r[b], k) for r in rows)
    losses = sum(within(r[b], k) and not within(r[a], k) for r in rows)
    n = wins + losses
    return wins, losses, sum(comb(n, i) for i in range(wins, n + 1)) / 2 ** n if n else 1.0


def remove(folder):
    # Git writes its objects read-only, which stops rmtree on Windows.
    shutil.rmtree(folder, onexc=lambda func, path, _: (os.chmod(path, stat.S_IWRITE), func(path)))


def within(value, k):
    return value is not None and value <= k


def main():
    clones = Path(sys.argv[1]).resolve()
    cases = json.loads((HERE / 'benchmark.json').read_text(encoding='utf-8'))
    sorts = {(s['project'], s['commit'], s['dependent']): s['sort']
             for s in json.loads((HERE / 'sample.json').read_text(encoding='utf-8'))}
    scratch = Path(tempfile.mkdtemp(prefix='ep-history-measure-'))
    rows = []
    try:
        for project, head in PROJECTS.items():
            repo = clones / project
            modified = {sha: files for sha, _, files in commits(repo, head)}
            by_commit = defaultdict(list)
            for case in cases:
                if case['project'] == project:
                    by_commit[case['commit'], case['parent']].append(case)
            for (sha, parent), group in by_commit.items():
                tree = scratch / f'{project}-{sha[:12]}'
                tree.mkdir()
                with tarfile.open(fileobj=io.BytesIO(git(repo, 'archive', '--format=tar', parent, binary=True))) as bundle:
                    bundle.extractall(tree, filter='data')
                subprocess.run(['git', 'init', '-q'], cwd=tree, check=True)
                subprocess.run(['git', 'add', '-A'], cwd=tree, check=True, capture_output=True)
                listed = propose(tree, limit=max(KS), seconds=120)
                proposals = [set(p['files']) for p in listed['proposals']]
                present = {p for p in git(repo, 'ls-tree', '-r', '--name-only', parent).splitlines() if source(p)}
                history, used = co_change(repo, parent, present, modified)
                model = source_model(tree)
                for case in group:
                    d = case['dependent']
                    linked = any(e in model[d].imports or d in model[e].imports
                                 for e in case['edit'] if d in model and e in model)
                    rows.append({'project': project, 'commit': sha, 'dependent': d,
                                 'sort': sorts.get((project, sha, d)), 'linked': linked,
                                 'product': place(proposals, d, case['edit']),
                                 'product_control': place(proposals, d, case['control']),
                                 'cochange': place(history, d, case['edit']),
                                 'cochange_control': place(history, d, case['control']),
                                 'proposals': len(proposals), 'proposal_issues': listed['coverage'].get('issues', []),
                                 'history_commits': used, 'history_pairs': len(history)})
                print(project, sha[:9], [(r['product'], r['product_control'], r['cochange'], r['cochange_control'])
                                         for r in rows[-len(group):]], flush=True)
                remove(tree)
    finally:
        remove(scratch)
    for r in rows:
        r['combined'] = min((v for v in (r['product'] and r['product'] * 2, r['cochange'] and r['cochange'] * 2) if v),
                            default=None)
    (HERE / 'measure.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')

    signals = ('product', 'product_control', 'cochange', 'cochange_control', 'combined')
    lines = []
    for label, subset in ([('total', rows)] + [(p, [r for r in rows if r['project'] == p]) for p in PROJECTS]
                          + [(f'sample: {s}', [r for r in rows if r['sort'] == s]) for s in ('rule', 'sweep', 'unrelated')]
                          + [('linked at the parent', [r for r in rows if r['linked']]),
                             ('not linked', [r for r in rows if not r['linked']])]):
        lines.append(f'{label}: {len(subset)} dependents in {len({(r["project"], r["commit"]) for r in subset})} commits')
        for s in signals:
            lines.append(f'  {s:18}' + '  '.join(f'K={k}: {sum(within(r[s], k) for r in subset):3}' for k in KS))
    for a, b in (('product', 'product_control'), ('cochange', 'cochange_control'), ('combined', 'product'),
                 ('cochange', 'product')):
        wins, losses, p = sign_test(rows, a, b, 50)
        lines.append(f'K=50 {a} over {b}: {wins} discordant for, {losses} against, one-sided p = {p:.3g}')
    text = '\n'.join(lines)
    (HERE / 'summary.txt').write_text(text + '\n', encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
