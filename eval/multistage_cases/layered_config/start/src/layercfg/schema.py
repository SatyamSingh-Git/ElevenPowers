from dataclasses import dataclass

TYPES = ('str', 'int', 'float', 'bool', 'duration', 'size', 'list', 'choice')


def normalize_key(name):
    """Lower-case each dotted part, trim it and treat dashes as underscores."""
    return '.'.join(part.strip().lower().replace('-', '_') for part in name.strip().split('.'))


@dataclass(frozen=True)
class Option:
    key: str
    type: str
    default: str | None = None
    help: str = ''
    aliases: tuple = ()
    choices: tuple = ()
    minimum: str | None = None
    maximum: str | None = None
    secret: bool = False

    def __post_init__(self):
        if self.type not in TYPES:
            raise ValueError(f'{self.key}: unknown type {self.type!r}')
        if self.type == 'choice' and not self.choices:
            raise ValueError(f'{self.key}: a choice option needs choices')
        if (self.minimum is not None or self.maximum is not None) and self.type not in ('int', 'float', 'duration', 'size'):
            raise ValueError(f'{self.key}: only numeric options take a range')

    @property
    def section(self):
        return self.key.rpartition('.')[0]

    @property
    def name(self):
        return self.key.rpartition('.')[2]


@dataclass(frozen=True)
class Entry:
    """One raw value from a layer, before it is checked against the schema."""
    key: str
    raw: str
    source: str
    layer: str


class Schema:
    def __init__(self, options):
        self._options = {}
        self._aliases = {}
        for option in options:
            if normalize_key(option.key) != option.key or '.' not in option.key:
                raise ValueError(f'option key {option.key!r} must be lower-case section.name')
            if option.key in self._options:
                raise ValueError(f'duplicate option {option.key!r}')
            self._options[option.key] = option
        for option in options:
            for alias in option.aliases:
                alias = normalize_key(alias)
                if alias in self._options or alias in self._aliases:
                    raise ValueError(f'alias {alias!r} of {option.key!r} is already taken')
                self._aliases[alias] = option.key

    def __iter__(self):
        return iter(self._options.values())

    def __len__(self):
        return len(self._options)

    def __contains__(self, name):
        return self.resolve(name) is not None

    def resolve(self, name):
        """The option a key or alias names, or None."""
        key = normalize_key(name)
        return self._options.get(self._aliases.get(key, key))

    def names(self):
        """Every spelling the schema accepts: option keys, then aliases."""
        return [*self._options, *self._aliases]

    def aliases_of(self, key):
        return [alias for alias, target in self._aliases.items() if target == key]

    def sections(self):
        seen = {}
        for option in self:
            seen.setdefault(option.section, []).append(option)
        return seen
