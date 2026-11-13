"""The project's own test command, run under coverage.py, and which tests reached a function."""
from __future__ import annotations

import os
import shlex
import shutil
from pathlib import Path

RCFILE = '[run]\ndynamic_context = test_function\n'
REFUSAL = ("is not a direct pytest or unittest call; pass the command to analyse with --command, "
           "for example --command \"python -m pytest -q\"")


def _words(command: str) -> list[str]:
    try:
        words = shlex.split(command, posix=os.name != 'nt')
    except ValueError as exc:
        raise ValueError(f'{command!r} {REFUSAL}') from exc
    # Windows splitting keeps a word's quotes, and the argv list goes to no shell
    # that would remove them; `-k 'a or b'` would reach pytest still quoted.
    return [w[1:-1] if len(w) > 1 and w[0] == w[-1] and w[0] in '"\'' else w for w in words]


def _beside(executable: str) -> str:
    """The interpreter installed beside a pytest executable: the one whose site-packages it uses."""
    found = executable if Path(executable).parent != Path('.') else shutil.which(executable)
    if found:
        sibling = Path(found).parent / ('python.exe' if os.name == 'nt' else 'python')
        if sibling.is_file():
            return str(sibling)
    return 'python'


def wrap(command: str, rcfile: Path) -> list[str]:
    """`python -m coverage run --rcfile RC -m RUNNER OPTIONS…` for a direct pytest or unittest command."""
    words = _words(command)
    name = Path(words[0]).name.removesuffix('.exe') if words else ''
    if name in {'pytest', 'py.test'}:
        python, runner, options = _beside(words[0]), 'pytest', words[1:]
    elif name.startswith('python') and words[1:2] == ['-m'] and words[2:3] in (['pytest'], ['unittest']):
        python, runner, options = words[0], words[2], words[3:]
    else:
        raise ValueError(f'{command!r} {REFUSAL}')
    # Workers in other processes would record their lines without this run's contexts.
    if '-n' in options or any(o.startswith('-n') and o[2:].isdigit() for o in options) \
            or any(a == '-p' and b.startswith('xdist') for a, b in zip(options, options[1:])):
        raise ValueError(f'{command!r} runs tests in parallel workers; pass a serial command with --command')
    return [python, '-m', 'coverage', 'run', '--rcfile', str(rcfile), '-m', runner, *options]


def reached(report: dict, path: str, fn) -> tuple[set[str], bool]:
    """(tests whose context ran a body line, whether some body line ran only outside any test)."""
    contexts = report.get('files', {}).get(path, {}).get('contexts', {})
    tests, outside = set(), False
    for line in range(fn.first, fn.last + 1):
        names = contexts.get(str(line), [])
        named = {n for n in names if n}
        tests |= named
        outside |= bool(names) and not named
    return tests, outside
