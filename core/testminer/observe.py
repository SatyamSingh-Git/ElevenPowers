"""A real run of the person's program, kept as line numbers and file hashes, and the functions it ran."""
from __future__ import annotations

import hashlib
import json
import re
import signal
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from ..strength.scope import git
from .coverage_run import _beside
from .functions import functions

OBSERVED = '.elevenpowers/testminer-observed.json'
FORMS = 'pass the program as python SCRIPT ARGS... or python -m MODULE ARGS...'
INSTALL = 'coverage.py 7 is not importable by {python}; install it there: {python} -m pip install coverage'
STALE = 'changed since it was recorded; record again'
MAIN = ('import importlib.util, sys\n'
        'spec = importlib.util.find_spec(sys.argv[1])\n'
        'package = spec is not None and spec.submodule_search_locations is not None\n'
        'sys.exit(0 if spec and (not package or importlib.util.find_spec(sys.argv[1] + ".__main__")) else 1)\n')


def _coverage_major(python: str) -> int:
    try:
        done = subprocess.run([python, '-c', 'import coverage; print(coverage.version_info[0])'],
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return 0
    return int(done.stdout.strip()) if done.returncode == 0 and done.stdout.strip().isdigit() else 0


def _runs_as_module(python: str, name: str) -> bool:
    try:
        return subprocess.run([python, '-c', MAIN, name], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _launched(words: list[str]) -> str | None:
    """The interpreter the Windows `py` launcher would run for these words (`py`, or `py -3.11`)."""
    try:
        done = subprocess.run([*words, '-c', 'import sys; print(sys.executable)'], capture_output=True, text=True,
                              timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() if done.returncode == 0 and done.stdout.strip() else None


def _target(words: list[str]) -> tuple[str, list[str], str]:
    """(interpreter, what follows `coverage run`, the form kept in the record without arguments)."""
    name = Path(words[0]).name.removesuffix('.exe') if words else ''
    if name == 'py':
        # Never a console script: pytest installs a top-level py.py, and `-m py` would run it.
        version = words[1:2] if words[1:2] and re.fullmatch(r'-[23](\.\d+)?(-32|-64)?', words[1]) else []
        python = _launched(words[:1] + version)
        if python is None:
            raise ValueError(f'{" ".join(words)!r}: the py launcher found no interpreter; {FORMS}')
        words, name = [python, *words[1 + len(version):]], 'python'
    if name.startswith('python'):
        if words[1:2] == ['-m'] and len(words) > 2:
            return words[0], words[1:], f'python -m {words[2]}'
        if len(words) > 1 and not words[1].startswith('-'):
            return words[0], words[1:], f'python {Path(words[1]).as_posix()}'
    elif name:
        # A console script is run as the module of the same name, when that runs.
        python = _beside(words[0])
        module = name.replace('-', '_')
        if _runs_as_module(python, module):
            return python, ['-m', module, *words[1:]], f'python -m {module}'
    raise ValueError(f'{" ".join(words)!r}: {FORMS}')


def _tracked(root: Path) -> list[str]:
    try:
        listed = git(root, ['ls-files', '-z', '--cached', '--others', '--exclude-standard'], time.monotonic() + 60)
    except ValueError:
        raise ValueError('the project is not a Git repository; TestMiner lists its files with git ls-files') from None
    return [path for path in listed.split('\0') if path.endswith('.py') and (root / path).is_file()]


def _hashes(root: Path, paths) -> dict[str, str]:
    return {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths if (root / path).is_file()}


def record(root: Path, words: list[str]) -> tuple[int, dict | None]:
    """Run the command in the project, under coverage.py; (its exit status, the saved record or None)."""
    root = Path(root).resolve()
    python, rest, form = _target(words)
    if rest[0] != '-m' and Path(rest[0]).is_absolute():
        # An absolute path names the person's folders; the state file may be committed.
        script = Path(rest[0]).resolve()
        form = 'python ' + (script.relative_to(root).as_posix() if script.is_relative_to(root) else script.name)
    if _coverage_major(python) < 7:
        raise ValueError(INSTALL.format(python=python))
    arguments = len(rest) - (2 if rest[0] == '-m' else 1)
    tracked = _tracked(root)
    before = _hashes(root, tracked)
    with tempfile.TemporaryDirectory(prefix='ep-record-') as folder:
        rc = Path(folder) / 'rc'
        rc.write_text(f'[run]\ndata_file = {Path(folder) / "data"}\nsource = {root}\nrelative_files = True\n'
                      'sigterm = true\n', encoding='utf-8')
        # A handler, not SIG_IGN: an ignored SIGINT is inherited and the program would ignore Ctrl-C too.
        # Ctrl-C reaches the program; TestMiner waits for coverage.py to save.
        previous = signal.signal(signal.SIGINT, lambda *_: None)
        try:
            status = subprocess.run([python, '-m', 'coverage', 'run', '--rcfile', str(rc), *rest], cwd=root).returncode
        finally:
            signal.signal(signal.SIGINT, previous)
        if not (Path(folder) / 'data').exists():
            return status, None
        output = Path(folder) / 'coverage.json'
        subprocess.run([python, '-m', 'coverage', 'json', '--rcfile', str(rc), '-q', '-o', str(output)], cwd=root,
                       capture_output=True)
        if not output.exists():
            return status, None
        report = json.loads(output.read_text(encoding='utf-8'))
    after = _hashes(root, tracked)
    files = {}
    for name, item in report.get('files', {}).items():
        path = name.replace('\\', '/')
        if path in before and item.get('executed_lines'):
            files[path] = {'sha256': before[path] if after.get(path) == before[path] else None,
                           'lines': sorted(item['executed_lines'])}
    if not files:
        return status, None
    observation = {'schema': 1, 'command': form, 'arguments': arguments,
                   'recorded': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'files': files}
    (root / '.elevenpowers').mkdir(exist_ok=True)
    (root / OBSERVED).write_text(json.dumps(observation, indent=2), encoding='utf-8')
    return status, observation


def observed(root: Path):
    """(functions a recorded run executed, those in files changed since, issues)."""
    try:
        observation = json.loads((root / OBSERVED).read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise ValueError('no recorded run; run: ep_testminer.py record -- COMMAND') from None
    current, stale, issues = [], [], []
    for path, item in sorted(observation['files'].items()):
        if not (root / path).is_file():
            issues.append(f'{path}: recorded, but no longer in the project')
            continue
        data = (root / path).read_bytes()
        lines = set(item['lines'])
        try:
            spans = functions(data.decode('utf-8-sig'))
        except (SyntaxError, UnicodeDecodeError):
            issues.append(f'{path}: recorded, but Python cannot parse it now')
            continue
        # A changed file's lines may have moved: those functions are named, never judged.
        same = item['sha256'] == hashlib.sha256(data).hexdigest()
        for fn in spans:
            if lines & set(range(fn.first, fn.last + 1)):
                (current if same else stale).append((path, fn))
    return current, stale, issues
