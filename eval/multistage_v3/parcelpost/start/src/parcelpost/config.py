"""Settings: built-in defaults, overridden by `parcelpost.ini` in the data directory."""
from configparser import ConfigParser
from dataclasses import dataclass, replace
from datetime import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .core.errors import ConfigError
from .formats.labels import LABEL_FORMATS

SETTINGS_FILE = "parcelpost.ini"
SECTION = "parcelpost"


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    fuel_percent: Decimal = Decimal("7.5")
    vat_percent: Decimal = Decimal("20")
    stale_hours: int = 48
    cutoff: time = time(17, 0)
    default_service: str = "ground"
    depot: str = "BHX"
    label_format: str = "text"

    @property
    def store_path(self):
        return self.data_dir / "shipments.json"

    @property
    def events_path(self):
        return self.data_dir / "events.jsonl"

    @property
    def accounts_path(self):
        return self.data_dir / "accounts.json"

    @property
    def addresses_path(self):
        return self.data_dir / "addresses.json"

    @property
    def manifest_dir(self):
        return self.data_dir / "manifests"

    @property
    def labels_dir(self):
        return self.data_dir / "labels"

    @property
    def invoices_dir(self):
        return self.data_dir / "invoices"


def _percent(text):
    value = Decimal(text)
    if not value.is_finite() or value < 0:
        raise ValueError(text)
    return value


def _hours(text):
    value = int(text)
    if value <= 0:
        raise ValueError(text)
    return value


def _time_of_day(text):
    hours, minutes = text.split(":")
    return time(int(hours), int(minutes))


def _word(text):
    if not text.strip() or len(text.split()) != 1:
        raise ValueError(text)
    return text.strip()


def _label_format(text):
    if text.strip() not in LABEL_FORMATS:
        raise ValueError(text)
    return text.strip()


_PARSERS = {
    "fuel_percent": _percent,
    "vat_percent": _percent,
    "stale_hours": _hours,
    "cutoff": _time_of_day,
    "default_service": _word,
    "depot": _word,
    "label_format": _label_format,
}


def load_settings(data_dir):
    data_dir = Path(data_dir)
    settings = Settings(data_dir=data_dir)
    path = data_dir / SETTINGS_FILE
    if not path.is_file():
        return settings
    parser = ConfigParser()
    parser.read(path, encoding="utf-8")
    if not parser.has_section(SECTION):
        return settings
    changes = {}
    for key, text in parser.items(SECTION):
        if key not in _PARSERS:
            raise ConfigError(f"unknown setting: {key}")
        try:
            changes[key] = _PARSERS[key](text)
        except (ValueError, InvalidOperation):
            raise ConfigError(f"invalid value for {key}: {text}") from None
    return replace(settings, **changes)
