"""One virtual environment per held-out repository: its test dependencies, not itself.

Grading and mining used to share the host interpreter, where an installed copy of
the package can already contain the answer. Here the repository's own
distribution is installed (to pull its runtime and test dependencies) and then
uninstalled, and a canary from a neutral directory confirms none of its import
names still resolves. The order in which test dependencies are looked for is
fixed: PEP 735 group, then an extra, then a requirements file, then pytest alone.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import tomllib
import zipfile

from core.process import run
from .bundle import GIT

GROUPS = ('test', 'tests', 'testing', 'dev')
EXTRAS = ('test', 'tests', 'testing', 'dev', 'all')
REQUIREMENTS = ('requirements-test.txt', 'requirements-tests.txt', 'test-requirements.txt',
                'requirements/test.txt', 'requirements/tests.txt', 'requirements-dev.txt', 'requirements/dev.txt')
TEST_DIRS = ('tests', 'test', 'testing')


def _pyproject(repo):
    path = Path(repo) / 'pyproject.toml'
    return tomllib.loads(path.read_text(encoding='utf8')) if path.is_file() else {}


def install_plan(repo):
    data = _pyproject(repo)
    groups = data.get('dependency-groups', {})
    extras = data.get('project', {}).get('optional-dependencies', {})
    if group := next((g for g in GROUPS if g in groups), None):
        plan = [['install', '.', '--group', group]]
    elif extra := next((e for e in EXTRAS if e in extras), None):
        plan = [['install', f'.[{extra}]']]
    elif requirements := next((r for r in REQUIREMENTS if (Path(repo) / r).is_file()), None):
        plan = [['install', '.'], ['install', '-r', requirements]]
    else:
        plan = [['install', '.']]
    return plan + [['install', 'pytest']]


def layout(repo, import_names):
    repo = Path(repo)
    test_dir = next((d for d in TEST_DIRS if (repo / d).is_dir()), None)
    if not test_dir:
        return None
    for name in import_names:
        for base, pythonpath in (('src', 'src'), ('', '.')):
            folder = repo / base / name
            if folder.is_dir():
                return {'source_dir': 'src/' if base else f'{name}/', 'test_dir': f'{test_dir}/', 'pythonpath': pythonpath}
            if folder.with_suffix('.py').is_file():
                return {'source_dir': f'{base}/{name}.py'.lstrip('/'), 'test_dir': f'{test_dir}/', 'pythonpath': pythonpath}
    return None


def canary(python, import_names, cwd):
    environment = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
    return all(run([python, '-c', f'import {name}'], cwd=Path(cwd), timeout=60, shell=False,
                   env=environment).returncode != 0 for name in import_names)


def importable(python, import_names, repo, pythonpath):
    """The canary's other direction: with its tracked source on the path, the package must import.

    Tracked files only, because that is all a task tree holds: a build that
    writes an ignored version module into the clone makes the clone import and
    every mined tree fail.
    """
    # Windows holds a handle a moment after a child exits; a strict cleanup turns that into a crash.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
        tree, archive = Path(scratch) / 'tree', Path(scratch) / 'tree.zip'
        done = run([*GIT, '-C', str(repo), 'archive', '--format=zip', '-o', str(archive), 'HEAD'],
                   cwd=Path(scratch), timeout=300, shell=False)
        if done.returncode:
            return False
        with zipfile.ZipFile(archive) as opened:
            opened.extractall(tree)
        environment = {**os.environ, 'PYTHONPATH': str(tree / pythonpath)}
        return all(run([python, '-c', f'import {name}'], cwd=Path(scratch), timeout=60, shell=False,
                       env=environment).returncode == 0 for name in import_names)


def _python(venv):
    return str(Path(venv) / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python'))


# pip records where each local install came from; that names the distribution for
# any build backend without parsing setup.py, setup.cfg or pyproject.toml.
DISTRIBUTION = '''import importlib.metadata as m, json, sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname
target = Path(sys.argv[1]).resolve()
for d in m.distributions():
    try:
        url = json.loads(d.read_text("direct_url.json") or "{}").get("url", "")
    except ValueError:
        continue
    if url.startswith("file:") and Path(url2pathname(urlparse(url).path)).resolve() == target:
        print(d.metadata["Name"])
        break'''


def _distribution(repo, python):
    done = run([python, '-c', DISTRIBUTION, str(repo)], cwd=Path(tempfile.gettempdir()), timeout=60, shell=False)
    return done.stdout.strip() if done.returncode == 0 else ''


IMPORT_NAMES = '''import importlib.metadata as m, json, sys
d = m.distribution(sys.argv[1])
top = (d.read_text("top_level.txt") or "").split()
if not top:
    top = sorted({p.parts[0].removesuffix(".py") for p in (d.files or [])
                  if p.parts and not p.parts[0].endswith((".dist-info", ".data")) and p.parts[0] != ".."
                  and (p.suffix == ".py" or len(p.parts) > 1)})
print(json.dumps([t for t in top if t.isidentifier()]))'''


def build(repo, venv):
    repo, venv = Path(repo), Path(venv)
    value = {'state': 'rejected', 'reason': '', 'python': _python(venv), 'import_names': [], 'plan': install_plan(repo)}
    steps = [[sys.executable, '-m', 'venv', str(venv)],
             [value['python'], '-m', 'pip', 'install', '-q', '--upgrade', 'pip>=25.1']]
    steps += [[value['python'], '-m', 'pip', '-q', *args] for args in value['plan']]
    for step in steps:
        done = run(step, cwd=repo, timeout=900, shell=False)
        if done.returncode:
            value['reason'] = 'environment step failed: ' + ' '.join(step[-3:])
            value['detail'] = (done.stdout + done.stderr)[-600:]
            return value
    name = _distribution(repo, value['python'])
    if not name:
        value['reason'] = 'distribution name unavailable'
        return value
    done = run([value['python'], '-c', IMPORT_NAMES, name], cwd=Path(tempfile.gettempdir()), timeout=60, shell=False)
    names = json.loads(done.stdout) if done.returncode == 0 else []
    if not names:
        value['reason'] = 'import names unavailable'
        return value
    value['import_names'] = names
    done = run([value['python'], '-m', 'pip', 'uninstall', '-y', '-q', name], cwd=repo, timeout=300, shell=False)
    if done.returncode:
        value['reason'] = 'package could not be uninstalled'
        return value
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as neutral:
        if not canary(value['python'], names, neutral):
            value['reason'] = 'package still importable after uninstall'
            return value
    found = layout(repo, names)
    if not found:
        value['reason'] = 'no recognisable source and test layout'
        return value
    if not importable(value['python'], names, repo, found['pythonpath']):
        value['reason'] = 'package does not import from its source tree'
        return value
    value.update(found, state='ready', reason='ready', distribution=name)
    return value
