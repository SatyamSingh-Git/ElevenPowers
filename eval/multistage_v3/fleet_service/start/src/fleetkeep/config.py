"""Fleet settings, read from the [fleet] section of a fleet's fleet.ini."""
import configparser
from dataclasses import dataclass

from .errors import FleetError
from .model.money import format_money, parse_money

SECTION = "fleet"


@dataclass(frozen=True)
class Settings:
    name: str = "fleet"
    labour_rate: int = 9500
    due_soon_miles: int = 500
    due_soon_days: int = 14
    max_daily_miles: int = 1000


def _count(text):
    value = int(text)
    if value < 0:
        raise ValueError(text)
    return value


def _name(text):
    if not text.strip():
        raise ValueError(text)
    return text.strip()


PARSERS = {
    "name": _name,
    "labour_rate": parse_money,
    "due_soon_miles": _count,
    "due_soon_days": _count,
    "max_daily_miles": _count,
}


def load_settings(path):
    parser = configparser.ConfigParser(default_section="defaults", interpolation=None)
    parser.read(path, encoding="utf-8")
    values = {}
    if parser.has_section(SECTION):
        for name, text in parser.items(SECTION):
            if name not in PARSERS:
                raise FleetError("E151", name=name)
            try:
                values[name] = PARSERS[name](text)
            except (ValueError, FleetError):
                raise FleetError("E152", name=name, value=text) from None
    return Settings(**values)


def write_settings(path, settings):
    parser = configparser.ConfigParser(interpolation=None)
    parser[SECTION] = {
        "name": settings.name,
        "labour_rate": format_money(settings.labour_rate),
    }
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        parser.write(handle)
