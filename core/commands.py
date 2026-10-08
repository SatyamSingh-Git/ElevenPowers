"""Conservative literal invocation qualification; never execute or rewrite a shell."""
from dataclasses import dataclass
from pathlib import Path
import re
import shlex


MAX_COMMAND = 16384
_CD = re.compile(r'''^cd[ \t]+(?P<path>"[^"\r\n]*"|'[^'\r\n]*'|[^\s'";&|<>]+)[ \t]*&&[ \t]*(?P<leaf>[^\r\n]+)$''')
_DYNAMIC = set('$`%!*?[]{};&|<>^~\r\n\0')


@dataclass(frozen=True)
class Invocation:
    command: str
    wrapped: bool = False
    issue: str = ''


def directory_issue(root, cwd=None):
    """Host metadata is a literal directory, never shell text."""
    try:
        project = Path(root).resolve(strict=True)
        if not project.is_dir():
            raise ValueError('not a directory')
        if cwd is None:
            return ''
        if not isinstance(cwd, str) or not cwd:
            raise ValueError('invalid directory')
        where = Path(cwd)
        where = (where if where.is_absolute() else project / where).resolve(strict=True)
        if not where.is_dir() or where != project:
            return 'tool working directory does not match the project root'
        return ''
    except (OSError, ValueError, RuntimeError):
        return 'tool working directory is unavailable or invalid'


def qualify(command, root, *, cwd=None):
    """Read one portable cd literal; the caller still requires an exact leaf."""
    text = command.strip()
    issue = directory_issue(root, cwd)
    if len(text) > MAX_COMMAND:
        return Invocation(text, issue='command exceeds invocation qualification budget')
    if not re.match(r'^cd(?:\s|$)', text):
        return Invocation(text, issue=issue)
    match = _CD.fullmatch(text)
    if not match:
        return Invocation(text, issue=issue or 'unsupported directory-wrapper syntax')
    raw = match['path']
    if (any(c in _DYNAMIC for c in raw) or
            ('\\' in raw and not raw.startswith(('"', "'")))):
        return Invocation(text, issue=issue or 'directory wrapper is not a portable literal')
    try:
        words = shlex.split(raw, posix=True)
        if len(words) != 1 or not words[0]:
            raise ValueError('invalid literal')
        directory = Path(words[0])
        project = Path(root).resolve(strict=True)
        directory = (directory if directory.is_absolute() else project / directory).resolve(strict=True)
        if not directory.is_dir() or directory != project:
            issue = issue or 'directory wrapper does not select the project root'
    except (OSError, ValueError, RuntimeError):
        issue = issue or 'directory wrapper target is unavailable or invalid'
    return Invocation(match['leaf'].strip(), wrapped=True, issue=issue)
