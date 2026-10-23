from dataclasses import dataclass


class ConfigError(Exception):
    """Base class for every configuration problem this package reports."""


class CoercionError(ConfigError):
    """A raw string could not be turned into the option's type."""


class ParseError(ConfigError):
    """The configuration file is not valid INI. Loading stops at the first one."""

    def __init__(self, name, line, message):
        super().__init__(f'{name} line {line}: {message}')
        self.name = name
        self.line = line
        self.message = message


@dataclass(frozen=True)
class Issue:
    source: str
    message: str

    def __str__(self):
        return f'{self.source}: {self.message}'


class ValidationError(ConfigError):
    """Every problem found while layering, reported together."""

    def __init__(self, issues):
        self.issues = list(issues)
        super().__init__('\n'.join(str(issue) for issue in self.issues))
