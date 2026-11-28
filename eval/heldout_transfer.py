"""Test transfer: do an agent's pinning tests also pass on the upstream fix it never saw?

docs/superpowers/specs/2026-11-28-heldout-test-transfer-design.md. Borrowed: SWT-bench's
measure of a generated test, fail before the repository's fix and pass after it
(Mündler et al., NeurIPS 2024). Added: the agent's own patch as a third tree, so only
tests that actually pin its change are judged. Three trees from the task's base: its
test files alone, its whole patch, and the upstream source change with its test files.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from core.surface import TEST_NAME
from .bundle import GIT, apply_patch
from .heldout_rehearse import gold
from .heldout_run import PATCHED, load_task
from .live import base_tree
from .vacuity_power import _signed_rank

TIMEOUT = 240
PASSED = re.compile(r'^PASSED (.+?)\s*$', re.MULTILINE)
ARMS = ('ordinary', 'instructed', 'superpowers', 'assisted')


def split(patch):
    """The patch's test files, as a patch of their own, and their paths."""
    kept, files = [], []
    for chunk in re.split(r'(?m)^(?=diff --git )', patch):
        found = PATCHED.match(chunk)
        if found and TEST_NAME.search(found[1]):
            kept.append(chunk)
            files.append(found[1])
    return ''.join(kept), sorted(files)


def passed(output):
    return set(PASSED.findall(output))


def _tree(task, root, patches):
    base_tree(task, root)
    for args in (['init', '-q'], ['add', '-A'], ['-c', 'user.email=e@e', '-c', 'user.name=e', 'commit', '-qm', 'base']):
        subprocess.run([*GIT, *args], cwd=root, capture_output=True)
    for patch in patches:
        problem = apply_patch(root, patch)
        if problem:
            return problem
    return ''


def _passing(task, root, files):
    environment = {**os.environ, **(task.source.get('env') or {}), 'PYTHONDONTWRITEBYTECODE': '1'}
    # One test file that cannot import would otherwise stop the session before the rest ran.
    done = subprocess.run([task.source['python'], '-m', 'pytest', *files, '-q', '-rA', '-p', 'no:cacheprovider',
                           '--continue-on-collection-errors'],
                          cwd=root, env=environment, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=TIMEOUT)
    return passed(done.stdout + done.stderr)


def transfer(task, patch, work):
    work = Path(work)
    # base_tree caches the task's archive beside each tree.
    work.mkdir(parents=True, exist_ok=True)
    tests, files = split(patch)
    _, upstream = gold(task)
    seen = {}
    for name, patches in (('without', [tests]), ('agent', [patch]), ('upstream', [upstream, tests])):
        problem = _tree(task, work / name, patches)
        if problem:
            return {'outcome': 'not measured', 'problem': f'{name}: {problem[:200]}', 'test_files': files}
        try:
            seen[name] = _passing(task, work / name, files)
        except subprocess.TimeoutExpired:
            return {'outcome': 'not measured', 'problem': f'{name}: tests timed out', 'test_files': files}
    pinning = sorted(seen['agent'] - seen['without'])
    transferring = [name for name in pinning if name in seen['upstream']]
    outcome = ('no pinning test' if not pinning else 'transfers' if len(transferring) == len(pinning)
               else 'partial' if transferring else 'none')
    return {'outcome': outcome, 'test_files': files, 'pinning': pinning, 'transferring': transferring}


def analyse(rows):
    """Per arm, the outcomes; primary, instructed against assisted over tasks, both pinning."""
    measured = [r for r in rows if r['outcome'] not in ('not measured', 'no pinning test')]
    per_arm = {}
    for arm in sorted({r['arm'] for r in rows}, key=lambda a: ARMS.index(a) if a in ARMS else len(ARMS)):
        mine = [r for r in rows if r['arm'] == arm]
        outcomes = {}
        for r in mine:
            outcomes[r['outcome']] = outcomes.get(r['outcome'], 0) + 1
        pinning = sum(len(r.get('pinning', [])) for r in mine)
        per_arm[arm] = {'runs': len(mine), 'outcomes': outcomes, 'pinning_tests': pinning,
                        'transferring_tests': sum(len(r.get('transferring', [])) for r in mine)}
    tasks = {}
    for r in measured:
        tasks.setdefault(r['task'], {}).setdefault(r['arm'], []).append(r['outcome'] == 'transfers')
    differences, tied = {}, 0
    for task, arms in sorted(tasks.items()):
        if 'instructed' in arms and 'assisted' in arms:
            share = {arm: sum(arms[arm]) / len(arms[arm]) for arm in ('instructed', 'assisted')}
            difference = share['instructed'] - share['assisted']
            if difference:
                differences[task] = difference
            else:
                tied += 1
    return {'per_arm': per_arm,
            'primary': {'test': 'two-sided signed-rank over tasks, instructed - assisted share of runs whose '
                                'pinning tests all transfer', 'differences': differences, 'tied': tied,
                        'p': _signed_rank(list(differences.values()))}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=Path, required=True, help="a sweep's collected.json")
    parser.add_argument('--runs', type=Path, required=True, help='the folder holding each slot/patch.diff')
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True, help='outside any Git ancestor')
    parser.add_argument('--out', type=Path, required=True, help='rows, resumed if present')
    args = parser.parse_args()
    corpus = json.loads(args.corpus.read_text(encoding='utf-8'))
    rows = json.loads(args.out.read_text(encoding='utf-8')) if args.out.exists() else []
    done = {r['slot'] for r in rows}
    for record in json.loads(args.records.read_text(encoding='utf-8')):
        if record['state'] != 'graded' or not record['resolved'] or record['slot'] in done:
            continue
        patch = (args.runs / record['slot'] / 'patch.diff').read_text(encoding='utf-8')
        if not split(patch)[1]:
            continue
        value = transfer(load_task(corpus, record['task']), patch, args.work / record['slot'])
        rows.append({'slot': record['slot'], 'task': record['task'], 'arm': record['arm'], **value})
        args.out.write_text(json.dumps(rows, indent=1) + '\n', encoding='utf-8')
        print(f"{len(rows):3} {record['slot']:50} {value['outcome']} "
              f"{len(value.get('transferring', []))}/{len(value.get('pinning', []))}", flush=True)
    print(json.dumps(analyse(rows), indent=1))


if __name__ == '__main__':
    main()
