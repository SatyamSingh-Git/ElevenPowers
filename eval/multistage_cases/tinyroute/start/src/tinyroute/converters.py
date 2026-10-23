"""Typed path parameters: how a segment of a URL is matched, converted and rebuilt.

A converter has a ``regex`` that the raw (still percent-encoded) text must
match, ``to_python`` for the decoded text, and ``to_url`` for building a URL
from a value. ``to_url`` raises ``ValueError`` for a value the converter
would not match, so ``url_for`` never builds a URL that leads nowhere.
"""
import re
from urllib.parse import quote

from .errors import RouteError

DEFAULT = 'str'


class Converter:
    """Any text without a slash."""

    regex = '[^/]+'
    safe = ''

    def to_python(self, text):
        return text

    def to_url(self, value):
        text = quote(self.format(value), safe=self.safe)
        if not re.fullmatch(self.regex, text):
            raise ValueError(f'{value!r} does not match {self.regex}')
        return text

    def format(self, value):
        return str(value)


class IntConverter(Converter):
    regex = '[0-9]+'

    def to_python(self, text):
        return int(text)

    def format(self, value):
        if isinstance(value, bool):
            raise ValueError(f'{value!r} is not an integer')
        return str(value)


class SlugConverter(Converter):
    regex = '[a-z0-9]+(?:-[a-z0-9]+)*'


class PathConverter(Converter):
    """The rest of the path, slashes included."""

    regex = '.+'
    safe = '/'


CONVERTERS = {
    'str': Converter(),
    'int': IntConverter(),
    'slug': SlugConverter(),
    'path': PathConverter(),
}


def register(name, converter):
    """Make ``<name:...>`` available in patterns compiled from now on."""
    if not re.fullmatch('[a-z_]+', name):
        raise RouteError(f"parameter type names are lower-case letters and '_': {name!r}")
    CONVERTERS[name] = converter


def lookup(name):
    try:
        return CONVERTERS[name]
    except KeyError:
        raise RouteError(f"unknown parameter type '{name}'") from None
