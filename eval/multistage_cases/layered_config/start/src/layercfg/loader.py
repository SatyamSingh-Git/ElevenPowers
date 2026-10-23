"""Layering defaults, the file and the environment into one Config."""
from .coerce import check_range, coerce
from .envsource import ENV_PREFIX, read_env
from .errors import CoercionError, Issue, ValidationError
from .iniparse import parse
from .options import APP_SCHEMA


class Config:
    """The effective configuration: one typed value per option and where it came from."""

    def __init__(self, schema, values, sources, env_prefix=ENV_PREFIX):
        self.schema = schema
        self.env_prefix = env_prefix
        self._values = dict(values)
        self._sources = dict(sources)

    def _option(self, key):
        option = self.schema.resolve(key)
        if option is None:
            raise KeyError(key)
        return option

    def __getitem__(self, key):
        return self._values[self._option(key).key]

    def __contains__(self, key):
        return key in self.schema

    def get(self, key, default=None):
        """The value of an option, by key or alias; `default` if no option has that name."""
        option = self.schema.resolve(key)
        if option is None:
            return default
        return self._values[option.key]

    def source(self, key):
        """Where the value came from: `default`, `<file> line <n>` or `env <NAME>`."""
        return self._sources[self._option(key).key]

    def items(self):
        return [(option.key, self._values[option.key]) for option in self.schema]

    def as_dict(self):
        return dict(self.items())

    def __repr__(self):
        changed = sum(source != 'default' for source in self._sources.values())
        return f'<Config {len(self._values)} options, {changed} set>'


def _defaults(schema):
    values, sources = {}, {}
    for option in schema:
        values[option.key] = None if option.default is None else coerce(option, option.default)
        sources[option.key] = 'default'
    return values, sources


def _apply(schema, entries, values, sources):
    issues = []
    for entry in entries:
        option = schema.resolve(entry.key)
        if option is None:
            message = 'unknown variable' if entry.layer == 'env' else f"unknown key '{entry.key}'"
            issues.append(Issue(entry.source, message))
            continue
        try:
            value = coerce(option, entry.raw)
        except CoercionError as error:
            issues.append(Issue(entry.source, f'{option.key}: {error}'))
            continue
        problem = check_range(option, value)
        if problem:
            issues.append(Issue(entry.source, f'{option.key}: {problem}'))
            continue
        values[option.key] = value
        sources[option.key] = entry.source
    return issues


def load(file_text=None, env=None, *, file_name='config.ini', schema=APP_SCHEMA, env_prefix=ENV_PREFIX):
    """Defaults, then the file, then the environment; later layers win.

    Every problem in every layer is collected and raised together as one
    ValidationError. A file that is not valid INI raises ParseError.
    """
    values, sources = _defaults(schema)
    entries = []
    if file_text is not None:
        entries += parse(file_text, file_name)
    if env:
        entries += read_env(env, env_prefix)
    issues = _apply(schema, entries, values, sources)
    if issues:
        raise ValidationError(issues)
    return Config(schema, values, sources, env_prefix)
