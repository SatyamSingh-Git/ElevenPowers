"""Per-project settings, read from surveytally.ini in the project folder.

    [surveytally]
    decimals = 1
    format = csv
    min_seconds = 120

Options given on the command line win over the file.
"""
import configparser
from dataclasses import dataclass, fields
from pathlib import Path

from ..model.errors import ConfigError
from ..reports.export import EXPORT_FORMATS

CONFIG_FILE = 'surveytally.ini'
SECTION = 'surveytally'


@dataclass(frozen=True)
class Settings:
    decimals: int = 1
    format: str = 'csv'
    min_seconds: int = 0


def load_settings(folder):
    path = Path(folder) / CONFIG_FILE
    if not path.is_file():
        return Settings()
    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding='utf-8')
    except configparser.Error as error:
        raise ConfigError(f'{CONFIG_FILE}: {error}') from None
    if not parser.has_section(SECTION):
        return Settings()
    section = parser[SECTION]
    known = {field.name for field in fields(Settings)}
    for key in section:
        if key not in known:
            raise ConfigError(f'{CONFIG_FILE}: unknown setting {key}')
    values = {}
    for key in ('decimals', 'min_seconds'):
        if key in section:
            values[key] = _whole_number(section, key)
    if 'format' in section:
        if section['format'] not in EXPORT_FORMATS:
            raise ConfigError(f'{CONFIG_FILE}: format must be one of {", ".join(EXPORT_FORMATS)}')
        values['format'] = section['format']
    return Settings(**values)


def _whole_number(section, key):
    value = section[key].strip()
    if not value.isdigit():
        raise ConfigError(f'{CONFIG_FILE}: {key} must be a whole number, got {value}')
    return int(value)
