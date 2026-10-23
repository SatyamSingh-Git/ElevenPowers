"""Multi-stage v2 oracles: behaviour groups, documented facts and project rules.

Each group runs alone in a private folder that is pytest's rootdir, with the
candidate only on PYTHONPATH, so a conftest the candidate left in its own tree
cannot collect, skip or rewrite the group.
"""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from core.process import run
from .bundle import GIT, export_patch
from .heldout_vacuity import vacuity

ROW = re.compile(r'^\|\s*`([^`]+)`\s*\|\s*`([^`]*)`\s*\|', re.M)
UNRELEASED = re.compile(r'^## Unreleased[ \t]*\n(.*?)(?=^## |\Z)', re.M | re.S)


def _active(case, stage):
    return [group for group in case['groups'] if group['since'] <= stage <= group['until']]


def groups(case, stage, tree, *, python=sys.executable, seconds=120):
    environment = {**os.environ, 'PYTHONPATH': str(Path(tree) / case['pythonpath']), 'PYTHONDONTWRITEBYTECODE': '1'}
    results = {}
    for group in _active(case, stage):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as private:
            target = Path(private) / f"test_{group['id']}.py"
            shutil.copyfile(Path(case['root']) / 'oracle' / 'groups' / f"{group['id']}.py", target)
            try:
                done = run([python, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--rootdir', private, str(target)],
                           cwd=Path(private), timeout=seconds, shell=False, env=environment)
                results[group['id']] = 'passed' if done.returncode == 0 else 'failed'
            except subprocess.TimeoutExpired:
                results[group['id']] = 'timeout'
    return results


def facts(text):
    return dict(ROW.findall(text))


def stale(case, stage, tree):
    """Expected facts documented wrongly or not at all, and removed ones still documented."""
    path = Path(tree) / case['docs']
    documented = facts(path.read_text(encoding='utf-8', errors='replace')) if path.is_file() else {}
    expected = case['facts'][stage]
    removed = set().union(*(case['facts'][n] for n in range(stage))) - set(expected)
    return sorted({key for key, value in expected.items() if documented.get(key) != value}
                  | {key for key in removed if key in documented})


def _bullets(path):
    if not path.is_file():
        return 0
    section = UNRELEASED.search(path.read_text(encoding='utf-8', errors='replace'))
    return len(re.findall(r'^- ', section.group(1), re.M)) if section else 0


def _bytes(path):
    return path.read_bytes() if path.is_file() else None


def _patch(before, after, work):
    shutil.copytree(before, work, ignore=shutil.ignore_patterns('.git'))
    for args in (['init', '-q'], ['add', '-A'], ['-c', 'user.email=e@e', '-c', 'user.name=e', 'commit', '-qm', 'before']):
        subprocess.run([*GIT, *args], cwd=work, capture_output=True, check=True)
    for path in [p for p in Path(work).iterdir() if p.name != '.git']:
        shutil.rmtree(path) if path.is_dir() else path.unlink()
    shutil.copytree(after, work, ignore=shutil.ignore_patterns('.git'), dirs_exist_ok=True)
    return export_patch(Path(work))


def rules(case, stage, before, after, *, python=sys.executable):
    before, after = Path(before), Path(after)
    result = {'changelog': max(0, _bullets(after / case['changelog']) - _bullets(before / case['changelog'])),
              'protected': _bytes(before / case['protected']) == _bytes(after / case['protected']),
              'test_with_fix': None}
    if case['stages'][stage - 1]['bugfix']:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
            patch = _patch(before, after, Path(scratch) / 'patch')
            value = vacuity(before, patch, python=python, env={'PYTHONPATH': case['pythonpath']},
                            test_dir=case['test_dir'], work=Path(scratch) / 'vacuity')['vacuous']
        result['test_with_fix'] = None if value is None else not value
    return result


def regressions(case, stage, previous, current):
    # A group retired at this stage is no longer required; one new at this stage was never passed before.
    return sorted(group['id'] for group in case['groups'] if stage <= group['until']
                  and previous.get(group['id']) == 'passed' and current.get(group['id']) != 'passed')
