"""Mutation score on the lines an agent's patch changed, per arm.

docs/superpowers/specs/2026-11-28-heldout-mutation-score-design.md. Borrowed: Cosmic Ray
8.7.0 through `core.strength.engines.cosmic`, the generator the product uses, confined to
the changed lines; each mutant judged as `eval.heldout_vacuity` judges the revert (the
task's interpreter and whole test directory, tests already red on the patch deselected, -x).
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from core.strength.engines import cosmic
from core.strength.execution import Budget
from core.surface import TEST_NAME
from .bundle import GIT, apply_patch
from .heldout_analyse import FOUR_ARMS, PAIRS, holm
from .heldout_run import load_task
from .heldout_vacuity import _suite
from .live import base_tree
from .vacuity_power import _signed_rank

CANDIDATES, RUN = 16, 8
HUNK = re.compile(r'^@@ -\S+ \+(\d+)(?:,(\d+))? @@')


def _git(root, *args):
    return subprocess.run([*GIT, *args], cwd=root, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=180)


def changed_lines(root):
    """Non-test `.py` files the patch changed, as Cosmic Ray's regions; staged, so new files count."""
    _git(root, 'add', '-A')
    regions, here = {}, None
    for line in _git(root, 'diff', '-U0', '--cached', 'HEAD').stdout.splitlines():
        if line.startswith('+++ '):
            path = line[4:].strip().removeprefix('b/')
            here = path if path.endswith('.py') and not TEST_NAME.search(path) else None
        elif here and (hunk := HUNK.match(line)):
            start, length = int(hunk[1]), int(hunk[2] or 1)
            if length:
                regions.setdefault(here, []).append([start, start + length - 1])
    return regions


def score(task, patch, work):
    root = Path(work) / 'tree'
    # base_tree caches the task's archive beside the tree.
    root.parent.mkdir(parents=True, exist_ok=True)
    base_tree(task, root)
    for args in (['init', '-q'], ['add', '-A'], ['-c', 'user.email=e@e', '-c', 'user.name=e', 'commit', '-qm', 'base']):
        _git(root, *args)
    problem = apply_patch(root, patch)
    if problem:
        return {'outcome': 'not measured', 'problem': problem[:200], 'mutants': 0, 'killed': 0}
    regions = changed_lines(root)
    if not regions:
        return {'outcome': 'no mutant', 'mutants': 0, 'killed': 0}
    candidates, _ = cosmic(root, sorted(regions), sys.executable, Budget(time.monotonic() + 120, CANDIDATES), regions)
    chosen = [c for c in candidates if c.relevance == 'changed_lines'][:RUN]
    if not chosen:
        return {'outcome': 'no mutant', 'mutants': 0, 'killed': 0}
    python, test_dir = task.source['python'], task.source['test_dir']
    environment = {**os.environ, **(task.source.get('env') or {}), 'PYTHONDONTWRITEBYTECODE': '1'}
    red, timed, _ = _suite(root, python, environment, test_dir, [])
    if timed:
        return {'outcome': 'not measured', 'problem': 'suite timed out', 'mutants': 0, 'killed': 0}
    deselect = [arg for node in sorted(red) for arg in ('--deselect', node)]
    killed, operators = 0, []
    for candidate in chosen:
        target = root / candidate.path
        original = target.read_bytes()
        target.write_text(candidate.content, encoding='utf-8')
        try:
            failing, timed, code = _suite(root, python, environment, test_dir, [*deselect, '-x'])
        finally:
            target.write_bytes(original)
        dead = timed or bool(failing) or code not in (0, 5)
        killed += dead
        operators.append([candidate.path, candidate.line, candidate.operator, dead])
    return {'outcome': 'scored', 'mutants': len(chosen), 'killed': killed, 'operators': operators}


def analyse(rows):
    scored = [r for r in rows if r['outcome'] == 'scored']
    per_arm = {}
    for arm in FOUR_ARMS:
        mine = [r for r in rows if r['arm'] == arm]
        if mine:
            per_arm[arm] = {'runs': len(mine), 'scored': sum(r['outcome'] == 'scored' for r in mine),
                            'no_mutant': sum(r['outcome'] == 'no mutant' for r in mine),
                            'mutants': sum(r['mutants'] for r in mine), 'killed': sum(r['killed'] for r in mine)}
    means = {}
    for r in scored:
        means.setdefault(r['task'], {}).setdefault(r['arm'], []).append(r['killed'] / r['mutants'])
    primary = {}
    for first, second in PAIRS:
        differences, tied = {}, 0
        for task, arms in sorted(means.items()):
            if first in arms and second in arms:
                difference = sum(arms[first]) / len(arms[first]) - sum(arms[second]) / len(arms[second])
                if difference:
                    differences[task] = difference
                else:
                    tied += 1
        primary[f'{first} - {second}'] = {'differences': differences, 'tied': tied,
                                           'p': _signed_rank(list(differences.values()))}
    for value, adjusted in zip(primary.values(), holm([value['p'] for value in primary.values()])):
        value['holm_p'] = adjusted
    return {'per_arm': per_arm, 'primary': primary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=Path, required=True, help="a sweep's collected.json")
    parser.add_argument('--runs', type=Path, required=True, help='the folder holding each slot/patch.diff')
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True, help='outside any Git ancestor')
    parser.add_argument('--out', type=Path, required=True, help='rows, resumed if present')
    parser.add_argument('--worker', type=int, default=0)
    parser.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    corpus = json.loads(args.corpus.read_text(encoding='utf-8'))
    rows = json.loads(args.out.read_text(encoding='utf-8')) if args.out.exists() else []
    done = {r['slot'] for r in rows}
    eligible = [r for r in json.loads(args.records.read_text(encoding='utf-8'))
                if r['state'] == 'graded' and r['resolved']]
    for index, record in enumerate(eligible):
        if index % args.workers != args.worker or record['slot'] in done:
            continue
        patch = (args.runs / record['slot'] / 'patch.diff').read_text(encoding='utf-8')
        value = score(load_task(corpus, record['task']), patch, args.work / record['slot'])
        rows.append({'slot': record['slot'], 'task': record['task'], 'arm': record['arm'], **value})
        args.out.write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8')
        print(f"{len(rows):3} {record['slot']:50} {value['outcome']} {value['killed']}/{value['mutants']}", flush=True)


if __name__ == '__main__':
    main()
