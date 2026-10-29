"""Branch settings, read from the `[lending]` section of `lending.ini`.

Every option has a default, so a library runs without the file. Options that
differ by material carry the material code after a dot, as in
`loan_days.DVD = 7`. Money is written in pounds and held in pence.
"""
from configparser import ConfigParser
from dataclasses import dataclass, field, replace

from ._generated import MATERIALS
from .errors import LendingError, refuse
from .model.calendar import WEEKDAYS
from .model.money import parse_money

FILE = 'lending.ini'
SECTION = 'lending'


@dataclass(frozen=True)
class Settings:
    loan_days: dict = field(default_factory=lambda: {'AB': 14, 'BK': 21, 'DVD': 7, 'MAG': 7})
    fine_per_day: dict = field(default_factory=lambda: {'AB': 25, 'BK': 25, 'DVD': 100, 'MAG': 10})
    max_fine: int = 1000
    block_at: int = 500
    max_renewals: int = 2
    max_holds: int = 10
    hold_pickup_days: int = 7
    notice_days: tuple = (7, 21)
    courtesy_days: int = 2
    closed_days: tuple = ()


def _count(text):
    value = int(text)
    if value < 0:
        raise ValueError(text)
    return value


def _day_list(text):
    return tuple(sorted({_count(part) for part in text.split(',') if part.strip()}))


def _weekday_list(text):
    names = tuple(part.strip().lower()[:3] for part in text.split(',') if part.strip())
    unknown = [name for name in names if name not in WEEKDAYS]
    if unknown or len(set(names)) == len(WEEKDAYS):
        raise ValueError(text)
    return names


CONVERTERS = {
    'loan_days': _count,
    'fine_per_day': parse_money,
    'max_fine': parse_money,
    'block_at': parse_money,
    'max_renewals': _count,
    'max_holds': _count,
    'hold_pickup_days': _count,
    'notice_days': _day_list,
    'courtesy_days': _count,
    'closed_days': _weekday_list,
}
PER_MATERIAL = ('loan_days', 'fine_per_day')


def load_settings(directory):
    settings = Settings()
    path = directory / FILE
    if not path.exists():
        return settings
    parser = ConfigParser()
    parser.optionxform = str
    parser.read(path, encoding='utf-8')
    if not parser.has_section(SECTION):
        return settings
    changes = {}
    for option, text in parser.items(SECTION):
        name, _, material = option.partition('.')
        if name not in CONVERTERS or bool(material) != (name in PER_MATERIAL):
            raise refuse('bad_setting', name=option, problem='unknown option')
        if material and material not in MATERIALS:
            raise refuse('bad_setting', name=option, problem=f'unknown material {material}')
        try:
            value = CONVERTERS[name](text.strip())
        except (ValueError, LendingError):
            raise refuse('bad_setting', name=option, problem=f'cannot read {text.strip()!r}') from None
        if material:
            changes.setdefault(name, dict(getattr(settings, name)))[material] = value
        else:
            changes[name] = value
    return replace(settings, **changes)
