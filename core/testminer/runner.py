"""Per function: do the project's tests reach it, and does emptying it fail any of them?

Report only. Every run is in a private copy; the person's tree gets only
`.elevenpowers/testminer.json`.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path

from ..config import load
from ..strength.baseline import outcomes
from ..strength.execution import Budget, execute
from ..strength.isolation import snapshot, trial
from ..strength.scope import select
from ..strength.settings import Settings
from .coverage_run import RCFILE, reached, wrap
from .functions import functions

INSTALL = 'coverage.py 7 is not importable in the test environment; install it there: python -m pip install coverage'
NOT_RUN = 'the selected tests did not run'
NEVER_RAN = 'no line of this file ran under the tests: never imported by them, or imported from an installed copy'


def _relative(root: Path, value: str) -> str:
    """The project-relative POSIX spelling coverage.py reports, however the person typed it."""
    path = Path(value)
    try:
        return (path if path.is_absolute() else root / path).resolve().relative_to(root).as_posix()
    except ValueError:
        raise ValueError(f'{value}: outside the project') from None


def _selected(root: Path, base: str, names, paths, deadline: float) -> list[tuple[str, object]]:
    # Keyed by line too: a property's getter and setter share one qualified name.
    found: dict[tuple[str, int], tuple[str, object]] = {}

    def spans(path):
        try:
            return functions((root / path).read_text(encoding='utf-8'))
        except SyntaxError as exc:
            raise ValueError(f'{path}: Python cannot parse it ({exc.msg}, line {exc.lineno})') from None

    for path in map(lambda p: _relative(root, p), paths):
        for fn in spans(path):
            found[path, fn.first] = path, fn
    for name in names:
        typed, _, qualified = name.partition('::')
        path = _relative(root, typed)
        match = [fn for fn in spans(path) if fn.name == qualified]
        if not match:
            raise ValueError(f'{name}: no such function')
        for fn in match:
            found[path, fn.first] = path, fn
    if base:
        sha = subprocess.run(['git', 'rev-parse', '--verify', base + '^{commit}'], cwd=root,
                             capture_output=True, text=True).stdout.strip()
        if not sha:
            raise ValueError(f'{base}: not a commit')
        scope = select(root, sha, deadline)
        if scope.issues:
            raise ValueError('; '.join(scope.issues))
        for path in scope.paths:
            if path.endswith('.py'):
                for fn in spans(path):
                    if any(start <= fn.last and fn.start <= end for start, end in scope.regions.get(path, [])) \
                            or any(fn.start <= line <= fn.last for line in scope.deletions.get(path, [])):
                        found[path, fn.first] = path, fn
    return sorted(found.values(), key=lambda item: (item[0], item[1].first))


def node(root: Path, files: list[str], context: str) -> str | None:
    """`tests.test_a.T.test_m` as `tests/test_a.py::T::test_m`, when the module is one file."""
    parts = context.split('.')
    for cut in range(len(parts) - 1, 0, -1):
        module = '/'.join(parts[:cut]) + '.py'
        if module in files:
            return module + '::' + '::'.join(parts[cut:])
        named = [f for f in files if f.endswith('/' + parts[cut - 1] + '.py') or f == parts[cut - 1] + '.py']
        if len(named) == 1:
            return named[0] + '::' + '::'.join(parts[cut:])
    return None


def _empty(path: Path, fn) -> None:
    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
    indent = lines[fn.body - 1][:len(lines[fn.body - 1]) - len(lines[fn.body - 1].lstrip())]
    lines[fn.body - 1:fn.last] = [indent + 'return None\n']
    path.write_text(''.join(lines), encoding='utf-8')


def _verdict(execution, argv, copy, deadline: float) -> tuple[str, str]:
    if execution.status == 'timed_out':
        return ('unknown', 'budget') if time.monotonic() >= deadline else ('checked', 'timed out')
    if execution.status != 'complete':
        return 'unknown', execution.reason or execution.status
    passed, failed, errors = outcomes(' '.join(argv), execution, copy)
    if execution.returncode == 0 and passed and not failed:
        return 'reached, not checked', ''
    if failed or errors:
        return 'checked', ''
    return 'unknown', NOT_RUN


def mine(root: Path, *, base: str = '', names=(), paths=(), command: str = '', seconds: float = 60,
         limit: int = 20, test_seconds: float = 15) -> dict:
    root = Path(root).resolve()
    if not (base or names or paths):
        raise ValueError('name what to examine: --base COMMIT, --function FILE::NAME or --path FILE')
    if subprocess.run(['git', 'rev-parse', '--git-dir'], cwd=root, capture_output=True).returncode:
        raise ValueError('the project is not a Git repository; TestMiner copies it with git ls-files')
    command = command or load(root).command_for('tests')
    if not command:
        raise ValueError('no test command found; pass one with --command')
    deadline = time.monotonic() + seconds
    budget = Budget(deadline, limit + 3)
    settings = Settings()
    with tempfile.TemporaryDirectory(prefix='ep-testminer-') as folder:
        rc = Path(folder) / 'rc'
        argv = wrap(command, rc)
        plain = argv[:1] + argv[6:]
        targets = _selected(root, base, names, paths, deadline)
        result = {'schema': 1, 'command': command, 'issues': [], 'functions': []}
        verdicts = {}

        def give(path, fn, verdict, reason='', tests=()):
            verdicts[path, fn.first] = {'path': path, 'name': fn.name, 'line': fn.first, 'verdict': verdict,
                                       'reason': reason, 'tests': sorted(tests)}

        for path, fn in targets[limit:]:
            give(path, fn, 'unknown', 'budget')
        chosen = targets[:limit]
        try:
            with snapshot(root, settings, deadline) as pristine:
                issue, report = _baseline(argv, rc, folder, pristine, settings, deadline, budget, test_seconds, root)
                if issue:
                    result['issues'].append(issue)
                    for path, fn in chosen:
                        give(path, fn, 'unknown', issue)
                else:
                    reach = {}
                    for path, fn in chosen:
                        tests, outside = reached(report, path, fn)
                        reach[path, fn.first] = tests
                        if fn.refused:
                            give(path, fn, 'unknown', fn.refused)
                        elif not report['files'].get(path, {}).get('executed_lines'):
                            # Not even its `def` lines ran: never imported, or imported from elsewhere.
                            give(path, fn, 'unknown', NEVER_RAN)
                        elif not tests:
                            give(path, fn, *(('unknown', 'reached outside any test (fixture, setUp or import)')
                                             if outside else ('not reached',)))
                    probe = [(p, f) for p, f in chosen if (p, f.first) not in verdicts]
                    selection = _selection(argv, plain, probe, reach, pristine, settings, deadline, budget,
                                           test_seconds, root)
                    for path, fn in probe:
                        if time.monotonic() >= deadline:
                            give(path, fn, 'unknown', 'budget')
                            continue
                        run = selection(reach[path, fn.first])
                        with trial(pristine, settings, deadline) as copy:
                            _empty(copy / path, fn)
                            execution = execute(run, copy, budget, test_seconds, shell=False, original=root)
                            give(path, fn, *_verdict(execution, run, copy, deadline),
                                 tests=reach[path, fn.first])
        except (OSError, ValueError, TimeoutError) as exc:
            result['issues'].append(str(exc))
            for path, fn in chosen:
                if (path, fn.first) not in verdicts:
                    give(path, fn, 'unknown', str(exc))
    result['functions'] = [verdicts[p, f.first] for p, f in targets]
    state = root / '.elevenpowers'
    state.mkdir(exist_ok=True)
    (state / 'testminer.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def _baseline(argv, rc, folder, pristine, settings, deadline, budget, seconds, root):
    """(issue, coverage report): the unmodified tests, green, with at least one test context."""
    with trial(pristine, settings, deadline) as copy:
        rc.write_text(RCFILE + f'data_file = {Path(folder) / "data"}\nsource = {copy}\nrelative_files = True\n',
                      encoding='utf-8')
        version = execute([argv[0], '-c', 'import coverage; print(coverage.version_info[0])'], copy, budget,
                          seconds, shell=False, original=root)
        if version.status != 'complete' or version.returncode or not version.stdout.strip().isdigit() \
                or int(version.stdout.strip()) < 7:
            return INSTALL, {}
        execution = execute(argv, copy, budget, seconds, shell=False, original=root)
        if execution.status != 'complete':
            return 'baseline ' + (execution.reason or execution.status), {}
        passed, failed, errors = outcomes(' '.join(argv), execution, copy)
        if execution.returncode or not passed or failed or errors:
            return 'baseline: the unmodified tests did not pass', {}
        output = Path(folder) / 'coverage.json'
        exported = execute([argv[0], '-m', 'coverage', 'json', '--rcfile', str(rc), '--show-contexts', '-q',
                            '-o', str(output)], copy, budget, seconds, shell=False, original=root)
        if exported.status != 'complete' or exported.returncode or not output.exists():
            return 'baseline: coverage.py could not export its data', {}
        report = json.loads(output.read_text(encoding='utf-8'))
    report['files'] = {name.replace('\\', '/'): item for name, item in report.get('files', {}).items()}
    if not any(n for item in report['files'].values() for names in item.get('contexts', {}).values() for n in names):
        return 'baseline: coverage.py recorded no test contexts', {}
    return '', report


def _selection(argv, plain, probe, reach, pristine, settings, deadline, budget, seconds, root):
    """A function from a function's tests to the command that runs only those, if that can be trusted."""
    runner = argv[7]
    every = sorted({t for p, f in probe for t in reach[p, f.first]})
    if runner == 'unittest':
        name = {t: t for t in every}
    else:
        name = {t: node(root, pristine.paths, t) for t in every}
    if not every or None in name.values():
        return lambda tests: plain
    head = plain[:3]
    check = head + sorted(set(name.values()))
    with trial(pristine, settings, deadline) as copy:
        execution = execute(check, copy, budget, seconds, shell=False, original=root)
        trusted = _verdict(execution, check, copy, deadline)[0] == 'reached, not checked'
    if not trusted:
        return lambda tests: plain
    return lambda tests: head + sorted({name[t] for t in tests})
