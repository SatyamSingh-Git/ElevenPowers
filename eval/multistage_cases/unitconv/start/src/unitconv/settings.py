"""Conversion settings, their defaults, and settings files of `key = value` lines."""
from dataclasses import dataclass, fields, replace

from .errors import SettingsError
from .rounding import MODES

DEFAULT_PRECISION = 6
MAX_PRECISION = 15
DEFAULT_ROUNDING = 'half_even'
STYLES = ('symbol', 'name')


def check_precision(precision):
    if not 0 <= precision <= MAX_PRECISION:
        raise SettingsError(f'precision must be between 0 and {MAX_PRECISION}')


@dataclass(frozen=True)
class Settings:
    precision: int = DEFAULT_PRECISION
    rounding: str = DEFAULT_ROUNDING
    style: str = 'symbol'

    def __post_init__(self):
        check_precision(self.precision)
        if self.rounding not in MODES:
            raise SettingsError(f"unknown rounding mode: '{self.rounding}'")
        if self.style not in STYLES:
            raise SettingsError(f"unknown style: '{self.style}'")


def overridden(settings, **values):
    """`settings` with every value that is not None replaced."""
    return replace(settings, **{key: value for key, value in values.items() if value is not None})


def load_settings(path):
    names = {field.name for field in fields(Settings)}
    values = {}
    with open(path, encoding='utf-8') as file:
        for number, line in enumerate(file, 1):
            line = line.split('#', 1)[0].strip()
            if not line:
                continue
            key, equals, value = (part.strip() for part in line.partition('='))
            if not equals or not key:
                raise SettingsError(f"line {number}: expected 'key = value'")
            if key not in names:
                raise SettingsError(f"unknown setting: '{key}'")
            values[key] = value
    if 'precision' in values:
        if not values['precision'].isdigit():
            raise SettingsError(f'precision must be between 0 and {MAX_PRECISION}')
        values['precision'] = int(values['precision'])
    return Settings(**values)
