"""Multi-stage v2 oracles: behaviour groups, documented facts and project rules.

A stage's groups run in one pytest session in a private folder that is pytest's
rootdir, with the candidate only on PYTHONPATH, so a conftest the candidate left
in its own tree cannot collect, skip or rewrite them. Verdicts are read from
JUnit XML, and a session that times out is rerun one group at a time.
"""
from collections import defaultdict
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from xml.etree import ElementTree

from core.process import run
from .bundle import GIT, export_patch
from .heldout_vacuity import vacuity

ROW = re.compile(r'^\|\s*`([^`]+)`\s*\|\s*`([^`]*)`\s*\|', re.M)
UNRELEASED = re.compile(r'^## Unreleased[ \t]*\n(.*?)(?=^## |\Z)', re.M | re.S)


def _active(case, stage):
    return [group for group in case['groups'] if group['since'] <= stage <= group['until']]


def _run(case, names, tree, python, seconds):
    environment = {**os.environ, 'PYTHONPATH': str(Path(tree) / case['pythonpath']), 'PYTHONDONTWRITEBYTECODE': '1'}
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as private:
        for name in names:
            shutil.copyfile(Path(case['root']) / 'oracle' / 'groups' / f'{name}.py', Path(private) / f'test_{name}.py')
        report = Path(private) / 'report.xml'
        # Without the flag one group the candidate cannot import ends the session for all of them.
        # Verdicts come from the XML; echoing a candidate's captured output can exceed the runner's cap.
        run([python, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '--continue-on-collection-errors',
             '--tb=no', '--show-capture=no',
             '--rootdir', private, f'--junitxml={report}', *[f'test_{name}.py' for name in names]],
            cwd=Path(private), timeout=seconds, shell=False, env=environment)
        outcomes = defaultdict(list)
        if report.is_file():
            for item in ElementTree.parse(report).iter('testcase'):
                # A passing or failing test names its module as classname; a collection error, as name.
                module = (item.get('classname') or item.get('name') or '').split('.')[0]
                outcomes[module].append(not any(child.tag in ('failure', 'error', 'skipped') for child in item))
    return {name: 'passed' if outcomes[f'test_{name}'] and all(outcomes[f'test_{name}']) else 'failed'
            for name in names}


def groups(case, stage, tree, *, python=sys.executable, seconds=120):
    names = [group['id'] for group in _active(case, stage)]
    try:
        return _run(case, names, tree, python, seconds)
    except subprocess.TimeoutExpired:
        results = {}
        # One run per group again, so the hang is charged to the groups that hang.
        for name in names:
            try:
                results.update(_run(case, [name], tree, python, seconds))
            except subprocess.TimeoutExpired:
                results[name] = 'timeout'
        return results


def facts(text):
    """Every value documented for each key; a key documented twice keeps both."""
    found = defaultdict(list)
    for key, value in ROW.findall(text):
        found[key].append(value)
    return dict(found)


def stale(case, stage, tree):
    """Expected facts documented wrongly or not at all, and removed ones still documented."""
    path = Path(tree) / case['docs']
    documented = facts(path.read_text(encoding='utf-8', errors='replace')) if path.is_file() else {}
    expected = case['facts'][stage]
    removed = set().union(*(case['facts'][n] for n in range(stage))) - set(expected)
    # Current only when the expected value is the one value documented: an old row left beside it is stale.
    return sorted({key for key, value in expected.items() if set(documented.get(key, [])) != {value}}
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
