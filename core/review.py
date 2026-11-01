"""Would anything notice if this change were undone? The reviewer's report.

The held-out VACUOUS method (`eval/heldout_vacuity.py`, the check behind the
84% -> 37% result) made runner-agnostic and pointed at a commit pair. The
change's edits and deletions of non-test files are put back to base, files it
added are kept, its tests stay, and the declared suite runs again. A third run
on the restored head tree replaces that method's pytest-only no-op control:
a suite that disagrees with itself cannot be trusted to show a difference.

Runs happen in a private detached worktree; the reviewer's checkout is never
touched. Report only: a verdict changes nothing. See
docs/superpowers/specs/2026-11-01-reviewer-report-design.md.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from . import process
from .config import load
from .evidence import Kind, Result
from .parsers import parse
from .stress import COLLECT_ERROR
from .surface import TEST_NAME

PINNED, NOT_PINNED, UNKNOWN = 'pinned', 'not pinned', 'unknown'
TIMEOUT = 300
GIT = ['git', '--literal-pathspecs']


def _git(root, *args, timeout=120):
    done = process.run([*GIT, *args], cwd=root, timeout=timeout, shell=False)
    if done.returncode != 0:
        raise ValueError(f"git {' '.join(args[:2])} failed: {(done.stderr or done.stdout).strip()[:300]}")
    return done.stdout


def _identity(root, ref):
    commit = _git(root, 'rev-parse', '--verify', '--end-of-options', f'{ref}^{{commit}}').strip()
    return {'ref': ref, 'commit': commit, 'tree': _git(root, 'rev-parse', f'{commit}^{{tree}}').strip()}


def _changed(root, base, head):
    fields = _git(root, 'diff', '--name-status', '-z', '--no-renames', base, head).split('\0')
    return list(zip(fields[0::2], fields[1::2]))


@contextmanager
def _worktree(root, commit):
    hold = Path(tempfile.mkdtemp(prefix='ep-review-'))
    tree = hold / 'tree'
    try:
        _git(root, 'worktree', 'add', '--detach', str(tree), commit)
        # Ordinary JS tests need their installed dependencies; copied, as core/strength
        # copies them, so a test cannot change the reviewer's own.
        if (root / 'node_modules').is_dir():
            shutil.copytree(root / 'node_modules', tree / 'node_modules', symlinks=True)
        yield tree, hold
    finally:
        subprocess.run(['git', 'worktree', 'remove', '--force', str(tree)], cwd=root, capture_output=True)
        shutil.rmtree(hold, ignore_errors=True)


def _run(name, command, tree, timeout):
    run = {'name': name, 'command': command, 'exit': None, 'seconds': 0.0, 'failing': [], 'named': False,
           'problem': ''}
    started = time.monotonic()
    # A same-size edit inside one second keeps a stale .pyc (mtime+size check), so the
    # undone tree would silently run the change; eval/heldout_vacuity measured it.
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    try:
        done = process.run(command, cwd=tree, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        run['problem'] = f'timed out after {timeout} seconds'
    except process.OutputLimitExceeded:
        run['problem'] = 'printed more output than can be read'
    except OSError as error:
        run['problem'] = f'could not start: {error}'
    else:
        output = (done.stdout or '') + (done.stderr or '')
        records = parse(command, output, done.returncode, tree)
        collect = set(COLLECT_ERROR.findall(output))
        run.update(exit=done.returncode, named=bool(collect) or any(r.kind is Kind.TEST for r in records),
                   failing=sorted({r.identity for r in records if r.kind is Kind.TEST and r.result is not Result.PASS}
                                  | collect))
    run['seconds'] = round(time.monotonic() - started, 2)
    return run


def _verdict(head, undone, again):
    for run in (head, undone, again):
        if run['problem']:
            return UNKNOWN, f"the {run['name']} run {run['problem']}", []
    if head['failing'] != again['failing'] or (head['exit'] == 0) != (again['exit'] == 0):
        return UNKNOWN, 'the suite gave different results on the same tree, so a difference cannot be trusted', []
    new = sorted(set(undone['failing']) - set(head['failing']))
    if new:
        return PINNED, f'{len(new)} test(s) fail with the change undone and pass with it', new
    if undone['exit'] == 0 or (head['named'] and undone['named'] and undone['exit'] != 0 and head['exit'] != 0):
        return NOT_PINNED, 'no test fails with the change undone that did not already fail with it', []
    if head['exit'] == 0:
        return PINNED, 'the suite fails with the change undone and passes with it, but named no test', []
    return UNKNOWN, 'the suite fails with the change too and named no test, so the runs cannot be compared', []


def _limits(report):
    limits = [f"Only `{report['command']}` was judged; another test command could notice what this one did not."
              if report['command'] else 'No test command was run.',
              'A test that fails with the change undone shows the change is noticed, not that it is right.',
              'The private checkout holds tracked files and node_modules only: a virtual environment or build '
              'output that lives inside the project is not there.']
    if report['kept']:
        limits.insert(0, f"{len(report['kept'])} file(s) the change added were kept when it was undone, so a "
                         'test that only imports them notices nothing.')
    return limits


def review(root, base, head='HEAD', *, command=None, timeout=TIMEOUT):
    root = Path(root).resolve(strict=True)
    command = command if command is not None else load(root).command_for('tests')
    report = {'schema': 1, 'base': _identity(root, base), 'head': _identity(root, head), 'command': command,
              'verdict': UNKNOWN, 'reason': '', 'pinning': [], 'named': False, 'runs': []}
    changed = _changed(root, report['base']['commit'], report['head']['commit'])
    report['tests'] = sorted(path for _, path in changed if TEST_NAME.search(path))
    report['undone'] = sorted(path for status, path in changed if status != 'A' and not TEST_NAME.search(path))
    report['kept'] = sorted(path for status, path in changed if status == 'A' and not TEST_NAME.search(path))
    if not command:
        report['reason'] = 'no test command is declared for this project; declare one or pass --command'
    elif not report['undone']:
        report['reason'] = ('the change only added files, which are kept when it is undone' if report['kept']
                            else 'the change touched only tests' if report['tests'] else 'nothing changed')
    else:
        with _worktree(root, report['head']['commit']) as (tree, hold):
            runs = report['runs']
            runs.append(_run('head', command, tree, timeout))
            if not runs[-1]['problem']:
                paths = hold / 'undone.txt'
                paths.write_bytes(b'\0'.join(p.encode('utf-8') for p in report['undone']))
                _git(tree, 'checkout', report['base']['commit'], f'--pathspec-from-file={paths}',
                     '--pathspec-file-nul')
                runs.append(_run('undone', command, tree, timeout))
                _git(tree, 'reset', '-q', '--hard', report['head']['commit'])
                runs.append(_run('head again', command, tree, timeout))
        verdict, reason, pinning = (_verdict(*runs) if len(runs) == 3
                                    else (UNKNOWN, f"the head run {runs[0]['problem']}", []))
        report.update(verdict=verdict, reason=reason, pinning=pinning, named=any(r['named'] for r in runs))
    report['unknown'] = _limits(report)
    return report
