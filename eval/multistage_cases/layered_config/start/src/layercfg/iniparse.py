"""The file layer: a small INI dialect.

    [section]
    key = value
    other = a long value
        continued on an indented line

Lines starting with `#` or `;` are comments. Keys are dotted with their
section, so `port` under `[server]` is `server.port`.
"""
import re

from .errors import ParseError
from .schema import Entry, normalize_key

_SECTION = re.compile(r'^\[([^\[\]]+)\]$')
COMMENT_PREFIXES = ('#', ';')


def parse(text, name):
    """Entries in file order. Later entries for the same key win when layered."""
    entries = []
    section = None
    pending = None
    for number, line in enumerate(text.lstrip('﻿').splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(COMMENT_PREFIXES):
            continue
        if line[0] in ' \t' and pending is not None:
            pending[1].append(stripped)
            continue
        if pending is not None:
            entries.append(_entry(*pending))
            pending = None
        header = _SECTION.match(stripped)
        if header:
            section = normalize_key(header.group(1))
            if not all(section.split('.')):
                raise ParseError(name, number, f"bad section name '{header.group(1)}'")
            continue
        key, equals, value = stripped.partition('=')
        if not equals or not key.strip():
            raise ParseError(name, number, "expected 'key = value' or '[section]'")
        if section is None:
            raise ParseError(name, number, 'key outside of a section')
        pending = (f'{section}.{normalize_key(key)}', [value.strip()], f'{name} line {number}')
    if pending is not None:
        entries.append(_entry(*pending))
    return entries


def _entry(key, parts, source):
    return Entry(key, ' '.join(part for part in parts if part), source, 'file')
