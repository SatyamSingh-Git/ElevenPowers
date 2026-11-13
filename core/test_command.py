"""The test command a project already declares in tox, make or CI.

Read, never run. A declaration is reduced to its runner and the paths it names:
placeholders, make variables, plugin flags and wrappers belong to the tool that
owns the line and fail outside it (cachetools' `--cov` exited 4 without pytest-cov).
"""
from __future__ import annotations

import configparser
import shlex
from pathlib import Path

MAX_BYTES = 256 * 1024
MAX_WORKFLOWS = 20
REFUSED = {'&&', '||', ';', '|'}


def _text(path: Path) -> str | None:
    try:
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            return None
        return path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return None


def reduce(root: Path, line: str, moved: bool = False) -> tuple[bool, str | None]:
    """(names a runner, its reduced command); a runner in a line we cannot trust gives None.

    `moved`: the line runs from another directory, so its paths and the tests it
    collects both differ from the project root's.
    """
    try:
        words = shlex.split(line, comments=True)
    except ValueError:
        return 'pytest' in line or 'unittest' in line, None
    if 'install' in words:
        return False, None
    for i, word in enumerate(words):
        if Path(word).name.removesuffix('.exe') in {'pytest', 'py.test'}:
            runner, rest = 'pytest', words[i + 1:]
        elif word == '-m' and words[i + 1:i + 2] in (['pytest'], ['unittest']):
            runner, rest = words[i + 1], words[i + 2:]
        else:
            continue
        if moved or any(w in REFUSED or w.endswith(';') for w in words):
            return True, None
        if runner == 'unittest':
            return True, 'python -m unittest discover' if rest[:1] == ['discover'] else 'python -m unittest'
        paths = [w for w in rest if not w.startswith('-') and (root / w.split('::')[0]).exists()]
        return True, ' '.join(['python -m pytest', *paths])
    return False, None


def _tox(root: Path):
    text = _text(root / 'tox.ini')
    if text is None:
        return
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read_string(text)
    except configparser.Error:
        return
    if parser.has_option('testenv', 'commands'):
        moved = parser.has_option('testenv', 'changedir')
        for line in parser.get('testenv', 'commands').splitlines():
            yield 'tox.ini', line, moved


def _make(root: Path):
    text = _text(root / 'Makefile')
    if text is None:
        return
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith('\t') and line.partition(':')[0].strip() == 'test' and ':' in line:
            for recipe in lines[i + 1:]:
                if not recipe.startswith('\t'):
                    return
                yield 'Makefile', recipe.strip().lstrip('@'), False


def _workflows(root: Path):
    folder = root / '.github' / 'workflows'
    if not folder.is_dir():
        return
    for path in sorted(p for p in folder.iterdir() if p.suffix in {'.yml', '.yaml'})[:MAX_WORKFLOWS]:
        text = _text(path)
        # This reader does not model steps, so a file that moves any step to
        # another directory is not read at all.
        if text is None or 'working-directory:' in text:
            continue
        source = path.relative_to(root).as_posix()
        lines = text.splitlines()
        for i, line in enumerate(lines):
            key = line.strip().removeprefix('- ').strip()
            if not key.startswith('run:'):
                continue
            value = key[4:].strip()
            if value not in {'|', '>', '|-', '>-'}:
                yield source, value, False
                continue
            indent = len(line) - len(line.lstrip())
            for body in lines[i + 1:]:
                if body.strip() and len(body) - len(body.lstrip()) <= indent:
                    break
                yield source, body.strip(), False


def declared(root: Path) -> tuple[str, str] | None:
    """(command, source) from the first line, in tox, make, then CI, that names a test runner."""
    for reader in (_tox, _make, _workflows):
        for source, line, moved in reader(root):
            names, command = reduce(root, line, moved)
            if names:
                return (command, source) if command else None
    return None
