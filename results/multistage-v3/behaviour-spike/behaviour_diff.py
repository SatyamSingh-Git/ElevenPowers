"""Spike: would recording behaviour under the pre-stage tests have flagged each lost dependent?

For one stage: copy the pre-stage tests onto the tree before and after the
stage, run them recording every project function's return values, and report
source files whose recorded behaviour changed although the agent did not edit
them. Uses only what the agent had: the project and its public tests.
"""
import filecmp
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).parent


def record(tree, tests_from, case, out):
    with tempfile.TemporaryDirectory() as work:
        copy = pathlib.Path(work) / 'tree'
        shutil.copytree(tree, copy)
        shutil.rmtree(copy / case['test_dir'], ignore_errors=True)
        shutil.copytree(pathlib.Path(tests_from) / case['test_dir'], copy / case['test_dir'])
        source = copy / case['pythonpath']
        env = {**os.environ, 'PYTHONPATH': os.pathsep.join([str(source), str(HERE)]),
               'PYTHONDONTWRITEBYTECODE': '1', 'BEHAVIOUR_SOURCE': str(source), 'BEHAVIOUR_OUT': str(out)}
        subprocess.run([sys.executable, '-m', 'pytest', case['test_dir'], '-q', '-p', 'no:cacheprovider',
                        '-p', 'behaviour_record'], cwd=copy, env=env, capture_output=True, timeout=600)
    return json.loads(pathlib.Path(out).read_text(encoding='utf-8')) if pathlib.Path(out).exists() else {}


def edited(before, after, root):
    changed = set()
    for path in (after / root).rglob('*.py'):
        other = before / path.relative_to(after)
        if not other.exists() or not filecmp.cmp(path, other, shallow=False):
            changed.add(path.relative_to(after).as_posix())
    return changed


def stage(before, after, case):
    with tempfile.TemporaryDirectory() as work:
        old = record(before, before, case, pathlib.Path(work) / 'old.json')
        new = record(after, before, case, pathlib.Path(work) / 'new.json')
    moved = set()
    for test, calls in old.items():
        for key, values in calls.items():
            if new.get(test, {}).get(key) != values:
                moved.add(key.split('::')[0])
    changed = edited(before, after, case['pythonpath'])
    return {'behaviour_changed': sorted(moved), 'edited': sorted(changed),
            'flagged': sorted(f for f in moved if f not in changed), 'tests_recorded': len(old)}
