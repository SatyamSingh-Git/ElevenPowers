"""VACUOUS, measured the way B7/B9 measured it, for a held-out candidate patch.

The candidate is applied to the base tree with no hidden tests. Tests already
red with the patch are deselected. The kill control puts the base version of
every changed non-test source file back: if the tree's own tests still pass,
they cannot tell the fix from its absence and the patch is VACUOUS. A survive
control (a no-op edit) must stay green, or the result is not scored. Copied in
method from `results/b7-mutants/probe.py`; only the interpreter and test
directory are parameters here.
"""
import os
from pathlib import Path
import re
import shutil
import subprocess

from core.surface import TEST_NAME
from .bundle import GIT

TIMEOUT = 240
FAILED = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)", re.MULTILINE)


def _suite(root, python, env, test_dir, extra):
    try:
        done = subprocess.run([python, '-m', 'pytest', test_dir, '-q', '-rA', '-p', 'no:cacheprovider', *extra],
                              cwd=root, env=env, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return set(), True, -1
    output = (done.stdout or '') + (done.stderr or '')
    return {m.group(1) for m in FAILED.finditer(output)}, False, done.returncode


def _git(root, *args, **kwargs):
    return subprocess.run([*GIT, *args], cwd=root, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=180, **kwargs)


def _changed_source(root):
    out, here = {}, None
    for line in _git(root, 'diff', '-U0', 'HEAD').stdout.splitlines():
        if line.startswith('+++ '):
            path = line[4:].strip().removeprefix('b/')
            here = path if path.endswith('.py') and not TEST_NAME.search(path) else None
        elif line.startswith('@@') and here:
            out.setdefault(here, True)
    return sorted(out)


def vacuity(base, patch, *, python, env, test_dir, work):
    root = Path(work)
    shutil.copytree(base, root)
    for args in (['init', '-q'], ['add', '-A'], ['-c', 'user.email=e@e', '-c', 'user.name=e', 'commit', '-qm', 'base']):
        _git(root, *args)
    if _git(root, 'apply', '--whitespace=nowarn', '-', input=patch).returncode:
        return {'vacuous': None, 'reason': 'patch did not apply'}
    changed = _changed_source(root)
    if not changed:
        return {'vacuous': None, 'reason': 'patch changed no source'}
    # A same-size revert inside one second keeps the patched .pyc (mtime+size check),
    # so the revert would silently not happen; measured 3 of 6 runs before this.
    environment = {**os.environ, **env, 'PYTHONDONTWRITEBYTECODE': '1'}
    red, timed, _ = _suite(root, python, environment, test_dir, [])
    if timed:
        return {'vacuous': None, 'reason': 'suite timed out'}
    deselect = [arg for node in sorted(red) for arg in ('--deselect', node)]
    saved = {rel: (root / rel).read_text(encoding='utf-8') for rel in changed if (root / rel).exists()}
    for rel in changed:
        old = _git(root, 'show', f'HEAD:{rel}')
        if old.returncode == 0:
            (root / rel).write_text(old.stdout, encoding='utf-8')
    try:
        failing, timed, code = _suite(root, python, environment, test_dir, [*deselect, '-x'])
    finally:
        for rel, body in saved.items():
            (root / rel).write_text(body, encoding='utf-8')
    killed = timed or bool(failing) or code not in (0, 5)
    first = changed[0]
    if first in saved:
        (root / first).write_text(saved[first] + '\n_ep_probe_noop = 0\n', encoding='utf-8')
        try:
            failing, timed, code = _suite(root, python, environment, test_dir, [*deselect, '-x'])
        finally:
            (root / first).write_text(saved[first], encoding='utf-8')
        if timed or failing or code not in (0, 5):
            return {'vacuous': None, 'reason': 'survive control failed'}
    return {'vacuous': not killed, 'reason': 'revert killed' if killed else 'revert survived'}
