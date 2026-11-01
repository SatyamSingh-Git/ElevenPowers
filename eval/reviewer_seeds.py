"""Seeds for the reviewer study (PLAN 13 A.3), from the kept v3 snapshots, at $0.

Per case, one stage of the superpowers arm's first conversation gives three
seeds over the same real change: C as the agent left it, U with the stage's
test changes taken back out, and W with one Cosmic Ray mutation on a changed
line that the stage's own tests miss and the case's behaviour oracle catches.
`judge` is the gate: what ep_review's frozen report says about each seed, before
any model sees one (eval/reviewer_run.py freezes the reports and applies it).
See docs/superpowers/specs/2026-11-01-reviewer-benefit-design.md.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from core import process
from core.review import NOT_PINNED, PINNED
from core.strength.engines import cosmic
from core.strength.execution import Budget
from core.strength.scope import select
from . import multistage_oracles as oracles
from .multistage_cases import load

GIT = ['git', '-c', 'user.email=seed@elevenpowers', '-c', 'user.name=seed', '-c', 'core.autocrlf=false']
TOOL_ROOT = Path(__file__).resolve().parents[1]
V3 = TOOL_ROOT / 'results' / 'multistage-v3'


def _git(root, *args):
    return subprocess.run([*GIT, *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def commit_pair(base_tree, head_tree, root):
    """A repository whose HEAD~1 holds base_tree and HEAD holds head_tree; returns the base commit."""
    shutil.copytree(base_tree, root)
    _git(root, 'init', '-q')
    _git(root, 'add', '-A')
    _git(root, 'commit', '-qm', 'base')
    base = _git(root, 'rev-parse', 'HEAD')
    for path in [p for p in root.iterdir() if p.name != '.git']:
        shutil.rmtree(path) if path.is_dir() else path.unlink()
    shutil.copytree(head_tree, root, dirs_exist_ok=True)
    _git(root, 'add', '-A')
    _git(root, 'commit', '-qm', 'head', '--allow-empty')
    return base


def without_tests(before, after, test_dir, out):
    """The change with its test changes taken back out, as the regrade's adversarial control did."""
    shutil.copytree(after, out)
    shutil.rmtree(out / test_dir, ignore_errors=True)
    if (before / test_dir).exists():
        shutil.copytree(before / test_dir, out / test_dir)
    return out


def wrong(tests_exit, kept, mutated):
    """The stage's tests pass with the mutant, and a group that passed without it does not."""
    return tests_exit == 0 and any(kept[g] == 'passed' and mutated.get(g) != 'passed' for g in kept)


def _tests(case, python):
    return f'"{python}" -m pytest {case["test_dir"]} -q -p no:cacheprovider'


def find(case, before, after, n, scratch, *, python=sys.executable, seconds=180, candidates=24):
    """The first candidate on stage n's changed lines that its tests miss and an oracle catches."""
    pair = scratch / 'pair'
    base = commit_pair(before, after, pair)
    deadline = time.monotonic() + seconds
    scope = select(pair, base, deadline)
    paths = [p for p in scope.paths if p.endswith('.py')]
    if scope.issues or not paths:
        return None
    found, _ = cosmic(pair, paths, python, Budget(deadline, candidates), {p: scope.regions[p] for p in paths})
    kept = oracles.groups(case, n, after)
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    for candidate in found:
        tree = scratch / 'mutant'
        shutil.rmtree(tree, ignore_errors=True)
        shutil.copytree(after, tree)
        (tree / candidate.path).write_text(candidate.content, encoding='utf-8', newline='')
        try:
            done = process.run(_tests(case, python), cwd=tree, timeout=120, env=env)
        except subprocess.TimeoutExpired:
            continue
        mutated = oracles.groups(case, n, tree) if done.returncode == 0 else {}
        if wrong(done.returncode, kept, mutated):
            return {'path': candidate.path, 'line': candidate.line, 'end_line': candidate.end_line,
                    'operator': candidate.operator, 'context': candidate.context, 'tree': tree,
                    'lost': sorted(g for g in kept if kept[g] == 'passed' and mutated.get(g) != 'passed')}
    return None


def build(out, batches, *, arm='superpowers', replicate=0, per_case=3):
    """Up to per_case W seeds per case; C and U come from the first, over the same change."""
    out = Path(out)
    analysis = json.loads((V3 / 'full-analysis.json').read_text(encoding='utf-8'))
    rerun = set(json.loads((V3 / 'full-rerun-c.json').read_text(encoding='utf-8')))
    vacuous = {(r['slot'], r['stage']): r['vacuous']
               for r in json.loads((V3 / 'vacuity' / 'stages.json').read_text(encoding='utf-8'))}
    seeds, searched = [], {}
    for row in sorted(analysis['rows'], key=lambda r: r['case']):
        if row['arm'] != arm or row['replicate'] != replicate:
            continue
        case = load(TOOL_ROOT / 'eval' / 'multistage_v3' / row['case'])
        folder = batches['c' if row['slot'] in rerun else 'b'] / row['slot']
        searched[row['case']], found = [], 0
        for stage in row['grade']['stages']:
            n = stage['stage']
            own = {g['id'] for g in case['groups'] if g['since'] == n}
            # A pinned, resolved stage, so C is a change a reviewer should accept.
            if not own <= set(stage['new']) or vacuous.get((row['slot'], n)) is not False:
                continue
            searched[row['case']].append(n)
            before, after = folder / 'snapshots' / str(n - 1), folder / 'snapshots' / str(n)
            with tempfile.TemporaryDirectory(prefix='ep-seed-', ignore_cleanup_errors=True) as scratch:
                hit = find(case, before, after, n, Path(scratch))
                if not hit:
                    continue
                found += 1
                kinds = [('W', hit['tree'])]
                if found == 1:
                    kinds = [('C', after), ('U', without_tests(before, after, case['test_dir'],
                                                               Path(scratch) / 'untested'))] + kinds
                for kind, head in kinds:
                    name = f"{row['case']}-{kind}" + (str(found) if kind == 'W' and found > 1 else '')
                    seed = {'seed': name, 'kind': kind, 'case': row['case'], 'slot': row['slot'], 'stage': n,
                            'request': case['stages'][n - 1]['request'], 'command': _tests(case, 'python'),
                            'base': commit_pair(before, head, out / name)}
                    if kind == 'W':
                        seed.update({k: hit[k] for k in ('path', 'line', 'end_line', 'operator', 'context', 'lost')})
                    seeds.append(seed)
            if found == per_case:
                break
    return {'schema': 1, 'arm': arm, 'replicate': replicate, 'per_case': per_case, 'seeds': seeds,
            'searched': searched, 'without_w': sorted(c for c in searched if not any(s['case'] == c for s in seeds))}


def judge(seed, report):
    """Did ep_review's report say what this seed needs it to say?"""
    unpinned = [(u['path'], u['line'], u['end_line']) for u in report['strength']['unpinned']]
    row = {'seed': seed['seed'], 'kind': seed['kind'], 'verdict': report['verdict'], 'unpinned': unpinned,
           'strength': report['strength']['state'], 'attempts': report['strength']['attempts']}
    if seed['kind'] == 'W':
        row['surfaced'] = any(path == seed['path'] and start - 2 <= seed['line'] <= end + 2
                              for path, start, end in unpinned)
    row['expected'] = {'C': report['verdict'] == PINNED, 'U': report['verdict'] == NOT_PINNED,
                       'W': row.get('surfaced', False)}[seed['kind']]
    return row


def tally(rows):
    return {kind: {'expected': sum(r['expected'] for r in rows if r['kind'] == kind),
                   'of': sum(r['kind'] == kind for r in rows)} for kind in 'CUW'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='a new folder outside this repository')
    parser.add_argument('--batch', type=Path, default=Path('E:/ep-runs/multistage-v3-full-2026-10-30-b'))
    parser.add_argument('--continuation', type=Path, default=Path('E:/ep-runs/multistage-v3-full-2026-10-30-c'))
    parser.add_argument('--results', type=Path, default=TOOL_ROOT / 'results' / 'reviewer-benefit')
    parser.add_argument('--per-case', type=int, default=3)
    args = parser.parse_args()
    if args.out.exists():
        parser.exit(2, 'the seed folder must be new\n')
    manifest = build(args.out, {'b': args.batch, 'c': args.continuation}, per_case=args.per_case)
    args.results.mkdir(parents=True, exist_ok=True)
    (args.results / 'seeds.json').write_text(json.dumps(manifest, indent=1), encoding='utf-8')
    print({kind: sum(s['kind'] == kind for s in manifest['seeds']) for kind in 'CUW'}, 'without W:', manifest['without_w'])


if __name__ == '__main__':
    main()
