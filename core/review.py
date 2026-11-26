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
import re
import shutil
import subprocess
import tempfile
import time

from . import process
from .config import load
from .evidence import Kind, Result
from .parsers import GRADLE, parse
from .strength import pit
from .strength.execution import Budget, execute
from .stress import COLLECT_ERROR, _with_outcomes
from .surface import TEST_NAME

PINNED, NOT_PINNED, UNKNOWN = 'pinned', 'not pinned', 'unknown'
TIMEOUT = 300
SHOWN = 10  # Pinning tests listed by name; read in a minute, not scrolled.
# Expected outputs and fixtures beside the tests are test material: undoing the code keeps them.
TEST_MATERIAL = re.compile(r'(^|/)(testdata|test_data|fixtures|__fixtures__|__snapshots__|golden)(/|$)')
# pytest's own words for a run that did not reach every test (-x, --maxfail, a collection error),
# and Maven's reactor summary for a module it never built after an earlier one failed. Maven -q
# prints no summary, so a stopped quiet build is not seen.
STOPPED = re.compile(r'^!+ (?:stopping after \d+ failures?|Interrupted: .*?) !+\s*$'
                     r'|^\[INFO\] \S.*? \.+ SKIPPED\s*$', re.MULTILINE)
# No hook runs in the private worktree: nothing undeclared is run.
GIT = ['git', '--literal-pathspecs', '-c', f'core.hooksPath={os.devnull}']


class GitFailed(ValueError):
    """Git ran and refused, as opposed to not finishing."""


def _git(root, *args, timeout=120):
    try:
        done = process.run([*GIT, *args], cwd=root, timeout=timeout, shell=False)
    except (subprocess.TimeoutExpired, process.OutputLimitExceeded) as error:
        raise ValueError(f"git {' '.join(args[:2])} did not finish: {error}") from None
    if done.returncode != 0:
        raise GitFailed(f"git {' '.join(args[:2])} failed: {(done.stderr or done.stdout).strip()[:300]}")
    return done.stdout


def _identity(root, ref):
    try:
        commit = _git(root, 'rev-parse', '--verify', '--end-of-options', f'{ref}^{{commit}}').strip()
    except GitFailed:
        # git says only "Needed a single revision", which does not say which one.
        raise ValueError(f'{ref!r} does not name a commit in this repository') from None
    return {'ref': ref, 'commit': commit, 'tree': _git(root, 'rev-parse', f'{commit}^{{tree}}').strip()}


def _changed(root, base, head):
    fields = _git(root, 'diff', '--name-status', '-z', '--no-renames', base, head).split('\0')
    return list(zip(fields[0::2], fields[1::2]))


def _base(root, base, head):
    """The base as named, or where head branched from it when it has moved on since."""
    try:
        _git(root, 'merge-base', '--is-ancestor', base['commit'], head['commit'])
        return base
    except GitFailed:
        pass
    try:
        fork = _git(root, 'merge-base', base['commit'], head['commit']).strip()
    except GitFailed:
        raise ValueError(f"{base['ref']!r} and {head['ref']!r} share no history") from None
    # Diffing from the moved tip would undo the base's own later edits and credit them to this change.
    return {**_identity(root, fork), 'ref': base['ref'], 'moved': base['commit']}


def _is_test(path):
    return bool(TEST_NAME.search(path) or TEST_MATERIAL.search(path))


@contextmanager
def _worktree(root, commit):
    """The head worktree, and the project's own folder inside it."""
    hold = Path(tempfile.mkdtemp(prefix='ep-review-'))
    tree = hold / 'tree'
    try:
        project = tree / _git(root, 'rev-parse', '--show-prefix').strip()
        _git(root, 'worktree', 'add', '--detach', str(tree), commit)
        # Ordinary JS tests need their installed dependencies; copied, as core/strength
        # copies them, so a test cannot change the reviewer's own. A tracked one is already there.
        if (root / 'node_modules').is_dir() and not (project / 'node_modules').exists():
            shutil.copytree(root / 'node_modules', project / 'node_modules', symlinks=True)
        yield tree, project, hold
    finally:
        # Twice: an interrupted `worktree add` leaves the worktree locked, and one --force refuses that.
        subprocess.run(['git', 'worktree', 'remove', '--force', '--force', str(tree)], cwd=root, capture_output=True)
        shutil.rmtree(hold, ignore_errors=True)


def _stopped(command, output, cwd):
    """Whether a run may not have reached every test.

    Gradle says nothing about the test tasks it never ran: without --continue, a failure in
    one subproject's tests ends the build before the next one's.
    """
    if STOPPED.search(output):
        return True
    if not GRADLE.search(command.lower()) or '--continue' in command or 'FAILURE: Build failed' not in output:
        return False
    settings = [Path(cwd) / name for name in ('settings.gradle', 'settings.gradle.kts')]
    return any(path.is_file() and re.search(r'^\s*include\b', path.read_text(encoding='utf-8', errors='replace'),
                                            re.MULTILINE) for path in settings)


def _run(name, command, cwd, timeout, original):
    # pytest names its passes too, so a run can be told apart from one that stopped early.
    command = _with_outcomes(command)
    run = {'name': name, 'command': command, 'exit': None, 'seconds': 0.0, 'failing': [], 'passed': [],
           'named': False, 'stopped': False, 'problem': ''}
    started = time.monotonic()
    # core/strength's runner: no bytecode is written (a same-size undo inside one second would
    # otherwise run the change's stale .pyc), and its guard catches a Python run that can
    # import the reviewer's checkout instead of this worktree.
    done = execute(command, cwd, Budget(time.monotonic() + timeout, 1), timeout, original=original)
    if done.status == 'timed_out':
        run['problem'] = f'timed out after {timeout} seconds'
    elif done.status == 'isolation_error':
        run['problem'] = ('could import your checkout instead of the private worktree '
                          '(an editable install, or PYTHONPATH pointing into it)')
    elif done.status != 'complete':
        run['problem'] = 'could not run, or printed more output than can be read'
    else:
        output = done.stdout + done.stderr
        tests = [r for r in parse(command, output, done.returncode, cwd) if r.kind is Kind.TEST]
        failing = {r.identity for r in tests if r.result is not Result.PASS}
        # The pattern also matches a setup error's `ERROR file.py::test`; keep only files no test names.
        collect = {path for path in COLLECT_ERROR.findall(output)
                   if not any(name.startswith(path + '::') for name in failing)}
        run.update(exit=done.returncode, named=bool(collect) or bool(tests), stopped=_stopped(command, output, cwd),
                   failing=sorted(failing | collect),
                   passed=sorted(r.identity for r in tests if r.result is Result.PASS))
    run['seconds'] = round(time.monotonic() - started, 2)
    return run


def _among(name, names):
    """The same test, or a file and a test inside it: `t.py` fails when `t.py::test` does."""
    return any(name == other or name.startswith(other + '::') or other.startswith(name + '::') for other in names)


def _broken(head, undone):
    """Tests that fail with the change and pass without it."""
    return sorted(name for name in head['failing']
                  if _among(name, undone['passed']) and not _among(name, undone['failing']))


def _verdict(head, undone, again):
    for run in (head, undone, again):
        if run['problem']:
            return UNKNOWN, f"the {run['name']} run {run['problem']}", []
    if head['failing'] != again['failing'] or (head['exit'] == 0) != (again['exit'] == 0):
        return UNKNOWN, 'the suite gave different results on the same tree, so a difference cannot be trusted', []
    unseen = [name for name in undone['failing'] if not _among(name, head['failing'])]
    # When head stopped early, only a test seen passing there can show a difference.
    new = [name for name in unseen if _among(name, head['passed'])] if head['stopped'] else unseen
    if new:
        return PINNED, (f"{len(new)} {'test fails' if len(new) == 1 else 'tests fail'} with the change "
                        f"undone and {'passes' if len(new) == 1 else 'pass'} with it"), sorted(new)
    if undone['stopped'] or len(unseen) > len(new):
        return UNKNOWN, 'a run stopped before every test had run, so finding no difference shows nothing', []
    if undone['exit'] == 0 or (head['named'] and undone['named'] and undone['exit'] != 0 and head['exit'] != 0):
        return NOT_PINNED, 'no test fails with the change undone that did not already fail with it', []
    if head['exit'] == 0:
        return PINNED, 'the suite fails with the change undone and passes with it, but named no test', []
    return UNKNOWN, 'the suite fails with the change too and named no test, so the runs cannot be compared', []


def _limits(report):
    limits = [f"Only \"{report['command']}\" was judged; another test command could notice what this one did not."
              if report['command'] else 'No test command was run.',
              'A test that fails with the change undone shows the change is noticed, not that it is right.',
              'The private checkout holds tracked files and node_modules only: a virtual environment or build '
              'output that lives inside the project is not there. Only Python runs are checked for importing '
              'your checkout instead.']
    if report['kept']:
        limits.insert(0, f"{len(report['kept'])} file(s) the change added were kept when it was undone, so a "
                         'test that only imports them notices nothing.')
    if report['strength']:
        limits += [f'Mutation analysis: {issue}' for issue in report['strength']['issues']]
        if report['strength'].get('own_tests'):
            limits.append(f'Mutation analysis: {pit.LIMITATION}')
        limits.append('A change to a line that no test noticed can behave the same as the original (an equivalent '
                      'mutant), so each unpinned line is a question to look at, not a proven gap.')
    if report.get('functions') and 'state' not in report['functions']:
        limits += [f'TestMiner: {issue}' for issue in report['functions']['issues']]
        limits.append('A value no test noticed can mean the same as what the function returns anyway, so a '
                      'function listed as not or partly checked is a question to look at, not a proven gap.')
    return limits


def _strength(tree, root, base, command, limits):
    """`core.strength` on the head worktree, under the project's strength settings and any overrides."""
    from dataclasses import replace
    from .ledger import Ledger
    from .strength.runner import analyze
    ledger = Ledger(root=tree, task='review', base=base)
    # The worktree has no project configuration; the reviewer's checkout does.
    config = load(root)
    ledger._config = replace(config, strength={**config.strength, **limits})
    value = analyze(ledger, base=base, command=command)
    lines = {}
    for item in value['observations']:
        if item['status'] == 'undetected':
            key = (item['path'], item['line'], item['end_line'], item['context'])
            # Cosmic Ray names `core/NumberReplacer`; PIT describes the change in words that can hold a `/`.
            operator = item['operator'] if item['id'].startswith('pit:') else item['operator'].rsplit('/', 1)[-1]
            lines.setdefault(key, []).append(operator)
    return {'state': value['state'], 'issues': value['issues'], 'summary': value['summary'],
            'attempts': value['attempts'], 'own_tests': pit.LIMITATION in value['limitations'],
            'limits': {key: value['settings'].get(key) for key in ('max_mutants', 'seconds')},
            'unpinned': [{'path': path, 'line': line, 'end_line': end, 'context': context, 'operators': operators}
                         for (path, line, end, context), operators in sorted(lines.items())]}


def _functions(project, base, command, seconds, limit, timeout):
    """TestMiner on the head worktree: a verdict per function the change touched."""
    from .testminer import runner
    try:
        return runner.mine(project, base=base, command=command, seconds=seconds, limit=limit, test_seconds=timeout)
    except (ValueError, OSError) as exc:
        return {'state': f'not measured: {exc}'}


def review(root, base, head='HEAD', *, command=None, timeout=TIMEOUT, strength=False, limits=None,
           functions=False, function_seconds=120, function_limit=20):
    root = Path(root).resolve(strict=True)
    command = command if command is not None else load(root).command_for('tests')
    head = _identity(root, head)
    report = {'schema': 1, 'base': _base(root, _identity(root, base), head), 'head': head, 'command': command,
              'verdict': UNKNOWN, 'reason': '', 'pinning': [], 'broken': [], 'named': False, 'runs': [],
              'strength': None, 'functions': None}
    changed = _changed(root, report['base']['commit'], report['head']['commit'])
    report['tests'] = sorted(path for _, path in changed if _is_test(path))
    report['undone'] = sorted(path for status, path in changed if status != 'A' and not _is_test(path))
    added = [path for status, path in changed if status == 'A' and not _is_test(path)]
    # A module the change turned into a package (pkg/mod.py -> pkg/mod/...): Python imports the
    # package before the restored module, so undoing the deletion also removes what replaced it.
    replaced = tuple(Path(path).with_suffix('').as_posix() + '/'
                     for status, path in changed if status == 'D' and not _is_test(path))
    report['removed'] = sorted(path for path in added if path.startswith(replaced))
    report['kept'] = sorted(path for path in added if path not in report['removed'])
    if not command:
        report['reason'] = 'no test command is declared for this project; declare one or pass --command'
    elif not report['undone']:
        report['reason'] = ('the change only added files, which are kept when it is undone' if report['kept']
                            else 'the change touched only tests' if report['tests'] else 'nothing changed')
    # Mutation still measures the lines of a change that only added files.
    if command and (report['undone'] or ((strength or functions) and report['kept'])):
        with _worktree(root, report['head']['commit']) as (tree, project, hold):
            runs = report['runs']
            if report['undone']:
                runs.append(_run('head', command, project, timeout, root))
            if runs and not runs[-1]['problem']:
                paths = hold / 'undone.txt'
                paths.write_bytes(b'\0'.join(p.encode('utf-8') for p in report['undone']))
                _git(tree, 'checkout', report['base']['commit'], f'--pathspec-from-file={paths}',
                     '--pathspec-file-nul')
                for path in report['removed']:
                    (tree / path).unlink()
                runs.append(_run('undone', command, project, timeout, root))
                _git(tree, 'reset', '-q', '--hard', report['head']['commit'])
                runs.append(_run('head again', command, project, timeout, root))
            if strength:
                report['strength'] = _strength(project, root, report['base']['commit'], command, limits or {})
            if functions:
                report['functions'] = _functions(project, report['base']['commit'], command, function_seconds,
                                                 function_limit, timeout)
        if runs:
            verdict, reason, pinning = (_verdict(*runs) if len(runs) == 3
                                        else (UNKNOWN, f"the head run {runs[0]['problem']}", []))
            report.update(verdict=verdict, reason=reason, pinning=pinning, named=any(r['named'] for r in runs))
            # Only from runs that agree with themselves; an unstable suite names nothing reliably.
            if len(runs) == 3 and runs[0]['failing'] == runs[2]['failing']:
                report['broken'] = _broken(runs[0], runs[1])
    report['unknown'] = _limits(report)
    return report


def _unpinned(strength, verdict):
    from .export import _text
    if strength is None:
        return ['Not measured. Run again with --strength to mutate the changed lines '
                '(Cosmic Ray for Python, Stryker for JavaScript and TypeScript).']
    counts, limits = strength['summary'], strength['limits']
    tried = counts['detected'] + counts['undetected']
    if strength['unpinned']:
        lines = [f"{counts['undetected']} of {tried} changes tried on the changed lines went unnoticed. "
                 'Each line below could be altered while every test still passes:', '']
        lines += [f"- {_text(item['path'])}:{item['line']} in {_text(item['context'] or 'module')}: "
                  + _text(', '.join(item['operators'])) for item in strength['unpinned'][:SHOWN]]
        if len(strength['unpinned']) > SHOWN:
            lines.append(f"- and {len(strength['unpinned']) - SHOWN} more lines; the JSON report lists them all")
    elif tried:
        lines = [f'All {tried} changes tried on the changed lines were noticed by a test.'
                 + (' The tests run these lines, but none of them tells the new behaviour from the old.'
                    if verdict == NOT_PINNED else '')]
    else:
        lines = [f"Not measured: {_text(strength['state'])}."]
    # A sample, not every line: say how big, and how to look further. Invalid settings leave no budget.
    if limits['max_mutants'] is not None:
        lines += ['', f"Budget: up to {limits['max_mutants']} mutations in {limits['seconds']:g} seconds; "
                      '--max-mutants and --mutation-seconds raise it.']
    return lines


def _unchecked(functions):
    from .export import _text
    from .testminer.runner import describe
    if functions is None:
        return ['Not measured. Run again with --functions to ask TestMiner which Python functions the change '
                'touched no test checks.']
    if 'state' in functions:
        return [f"Not measured: {_text(functions['state'].removeprefix('not measured: '))}."]
    items = functions['functions']
    if not items:
        return ['The change touched no Python function.']
    listed = [item for item in items if item['verdict'] in ('partly checked', 'reached, not checked', 'not reached')]
    lines = [f'- {_text(describe(item))}' for item in listed[:SHOWN]]
    if len(listed) > SHOWN:
        lines.append(f'- and {len(listed) - SHOWN} more; the JSON report lists them all')
    checked = sum(item['verdict'] == 'checked' for item in items)
    if checked:
        lines.append(f"{checked} function{'s' if checked > 1 else ''} the change touched "
                     f"{'are' if checked > 1 else 'is'} checked by {'their' if checked > 1 else 'its'} tests.")
    unknown = [item for item in items if item['verdict'] == 'unknown']
    if unknown:
        reasons = sorted({item['reason'] for item in unknown}, key=len)
        lines.append(f'{len(unknown)} could not be judged: ' + _text('; '.join(reasons)) + '.')
    return lines


def _listed(names):
    from .export import _text
    lines = [f'- {_text(name)}' for name in names[:SHOWN]]
    if len(names) > SHOWN:
        lines.append(f'- and {len(names) - SHOWN} more; the JSON report lists them all')
    return lines + ['']


def markdown(report):
    from .export import _text
    base, head = report['base']['commit'][:12], report['head']['commit'][:12]
    reason = report['reason'][:1].upper() + report['reason'][1:]
    lines = ['# Is this change pinned by its tests?', '', f"**{report['verdict'].upper()}.** {_text(reason)}.", '']
    if report['pinning']:
        lines += _listed(report['pinning'])
    elif report['verdict'] == PINNED:
        lines += ['The runner named no test, so which tests pin it is not known.', '']
    elif report['verdict'] == NOT_PINNED and not report['broken']:
        lines += ['Nothing in the suite would notice if this change were undone. '
                  'Ask for a test that fails without this change.', '']
    if report['broken']:
        count = len(report['broken'])
        lines += [f"The change breaks {count} {'test that passes' if count == 1 else 'tests that pass'} without it:"]
        lines += _listed(report['broken'])
    lines += [f"Change {base}..{head}: {len(report['undone'])} file(s) put back to base when undone, "
              f"{len(report['kept'])} added and kept, {len(report['tests'])} test file(s) changed."
              + (f" {len(report['removed'])} added file(s) replaced a deleted one and were removed with it."
                 if report['removed'] else '')
              + (f" {_text(report['base']['ref'])} has moved on to {report['base']['moved'][:12]} since this "
                 f"change branched, so it is compared from where it branched."
                 if report['base'].get('moved') else ''),
              '', '## Lines no test noticed', '', *_unpinned(report['strength'], report['verdict']),
              # .get: a report saved before 2026-11-22 has no functions entry.
              '', '## Functions no test checks', '', *_unchecked(report.get('functions')), '', '## What was run', '']
    trees = {'head': head, 'undone': f"{head} with {len(report['undone'])} file(s) put back to {base}",
             'head again': head}
    if report['runs']:
        lines += ['| run | tree | command | exit | failing | seconds |', '|---|---|---|---|---|---|']
        lines += ['| ' + ' | '.join([run['name'], trees[run['name']], _text(run['command']),
                                     _text(run['problem']) if run['problem'] else str(run['exit']),
                                     str(len(run['failing'])), str(run['seconds'])]) + ' |'
                  for run in report['runs']]
    else:
        lines.append('Nothing was run.')
    return '\n'.join(lines + ['', '## Unknown', ''] + [f'- {_text(limit)}' for limit in report['unknown']]) + '\n'
