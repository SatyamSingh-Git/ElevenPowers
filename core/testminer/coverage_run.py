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


def _workers(options: list[str]) -> str:
    """'parallel', 'serial' (an explicit -n 0) or '' for pytest-xdist options."""
    found = ''
    for i, option in enumerate(options):
        value = None
        if option in {'-n', '--numprocesses'}:
            value = options[i + 1] if i + 1 < len(options) else ''
        elif option.startswith('--numprocesses='):
            value = option.split('=', 1)[1]
        elif option.startswith('-n') and option[2:]:
            value = option[2:]
        elif option == '-p' and options[i + 1:i + 2] and options[i + 1].startswith('xdist'):
            found = found or 'parallel'
        if value is not None:
            found = 'serial' if value == '0' else 'parallel'
    return found


def _addopts(root: Path) -> list[str]:
    """`addopts` from every file pytest reads its configuration from."""
    import configparser
    import tomllib
    words = []
    for name, section in (('pytest.ini', 'pytest'), ('tox.ini', 'pytest'), ('setup.cfg', 'tool:pytest')):
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            parser.read(root / name, encoding='utf-8')
        except (configparser.Error, UnicodeError):
            continue
        if parser.has_option(section, 'addopts'):
            words += shlex.split(parser.get(section, 'addopts'))
    try:
        value = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf-8'))
        value = value.get('tool', {}).get('pytest', {}).get('ini_options', {}).get('addopts', [])
        words += shlex.split(value) if isinstance(value, str) else [str(v) for v in value]
    except (OSError, ValueError, AttributeError):
        pass
    return words


def wrap(command: str, rcfile: Path, root: Path | None = None) -> list[str]:
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
    # The command line comes after addopts, so its `-n 0` wins.
    workers = _workers(options)
    if workers == 'parallel':
        raise ValueError(f'{command!r} runs tests in parallel workers; pass a serial command with --command, '
                         'for example with -n 0')
    if runner == 'pytest' and root is not None and not workers and _workers(_addopts(root)) == 'parallel':
        raise ValueError("the project's pytest addopts run tests in parallel workers; pass --command with -n 0, "
                         'for example --command "python -m pytest -n 0"')
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
