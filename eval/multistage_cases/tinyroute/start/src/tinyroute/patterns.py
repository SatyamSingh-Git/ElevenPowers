"""Route patterns such as ``/users/<int:id>/posts/<slug>``."""
import re
from urllib.parse import unquote

from . import converters
from .errors import BuildError, RouteError

PARAMETER = re.compile(r'<(?:(?P<type>[a-z_]+):)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)>')


class Parameter:
    def __init__(self, name, type_name):
        self.name = name
        self.type = type_name
        self.converter = converters.lookup(type_name)

    def __repr__(self):
        return f'<{self.type}:{self.name}>'


class Pattern:
    """A compiled pattern: a list of literal strings and ``Parameter`` parts."""

    def __init__(self, text):
        if not text.startswith('/'):
            raise RouteError(f"pattern must start with '/': {text!r}")
        self.text = text
        self.parts = []
        position = 0
        for found in PARAMETER.finditer(text):
            self._literal(text[position:found.start()])
            if found['name'] in self.names:
                raise RouteError(f"parameter '{found['name']}' appears twice in {text!r}")
            self.parts.append(Parameter(found['name'], found['type'] or converters.DEFAULT))
            position = found.end()
        self._literal(text[position:])
        self.regex = re.compile(''.join(
            re.escape(part) if isinstance(part, str) else f'(?P<{part.name}>{part.converter.regex})'
            for part in self.parts))

    def _literal(self, text):
        if '<' in text or '>' in text:
            raise RouteError(f'malformed parameter in {self.text!r}')
        if text:
            self.parts.append(text)

    @property
    def parameters(self):
        return [part for part in self.parts if isinstance(part, Parameter)]

    @property
    def names(self):
        return [part.name for part in self.parameters]

    def match(self, path):
        """The converted parameters if ``path`` matches, otherwise None."""
        found = self.regex.fullmatch(path)
        if found is None:
            return None
        return {part.name: part.converter.to_python(unquote(found[part.name]))
                for part in self.parameters}

    def build(self, values, route):
        """The path for ``values``; ``route`` names the route in error messages."""
        pieces = []
        for part in self.parts:
            if isinstance(part, str):
                pieces.append(part)
                continue
            if part.name not in values:
                raise BuildError(f"missing parameter '{part.name}' for route '{route}'")
            try:
                pieces.append(part.converter.to_url(values[part.name]))
            except ValueError:
                raise BuildError(f"invalid value {values[part.name]!r} for parameter "
                                 f"'{part.name}' of route '{route}'") from None
        return ''.join(pieces)

    def __repr__(self):
        return f'Pattern({self.text!r})'
