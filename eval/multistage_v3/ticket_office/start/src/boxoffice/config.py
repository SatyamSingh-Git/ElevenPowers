"""Settings, read from the [boxoffice] section of boxoffice.ini in the data directory."""
from configparser import ConfigParser
from dataclasses import dataclass, fields, replace
from pathlib import Path

SETTINGS_FILE = "boxoffice.ini"
SECTION = "boxoffice"


@dataclass(frozen=True)
class Settings:
    theatre: str = "Box Office"
    currency: str = "GBP"
    booking_fee: int = 150
    hold_minutes: int = 15
    max_tickets_per_order: int = 10
    refund_cutoff_hours: int = 48


class SettingsError(ValueError):
    pass


def load_settings(root):
    """The defaults, overlaid with whatever boxoffice.ini in `root` sets."""
    path = Path(root) / SETTINGS_FILE
    if not path.is_file():
        return Settings()
    parser = ConfigParser()
    parser.read(path, encoding="utf-8")
    if not parser.has_section(SECTION):
        return Settings()
    known = {field.name: field.type for field in fields(Settings)}
    values = {}
    for key, raw in parser.items(SECTION):
        if key not in known:
            raise SettingsError(f"{SETTINGS_FILE}: unknown setting {key}")
        values[key] = _convert(key, raw, known[key])
    return replace(Settings(), **values)


def describe_settings(root):
    """Each setting with its value and whether boxoffice.ini or the default supplied it."""
    settings = load_settings(root)
    defaults = Settings()
    return [(field.name, getattr(settings, field.name),
             "default" if getattr(settings, field.name) == getattr(defaults, field.name) else SETTINGS_FILE)
            for field in fields(Settings)]


def _convert(key, raw, kind):
    if kind is not int:
        return raw.strip()
    try:
        value = int(raw)
    except ValueError:
        raise SettingsError(f"{SETTINGS_FILE}: {key} must be a whole number, got {raw!r}") from None
    if value < 0:
        raise SettingsError(f"{SETTINGS_FILE}: {key} cannot be negative")
    return value
