"""Site settings, read from ``settings.json`` in the data directory.

Every setting has a default, so the file is optional and may name only the
settings a site changes.
"""
from dataclasses import dataclass, fields
from pathlib import Path

from ..core.errors import ConfigError
from .jsonfile import number, read_json


@dataclass(frozen=True)
class Settings:
    stale_minutes: int = 30
    minutes_per_point: float = 2.0
    max_irrigation_minutes: int = 30
    dry_margin: float = 2.0
    max_offset: float = 5.0
    report_format: str = "text"
    light_on_lux: float = 10000.0
    ppfd_per_lux: float = 0.0185
    target_dli: float = 12.0
    vpd_low_kpa: float = 0.4
    vpd_high_kpa: float = 1.6
    condensation_margin: float = 2.0
    gap_minutes: int = 20
    archive_after_days: int = 90


def load_settings(path):
    path = Path(path)
    if not path.exists():
        return Settings()
    known = {field.name: field.type for field in fields(Settings)}
    values = {}
    for name, value in read_json(path).items():
        if name not in known:
            raise ConfigError(f"unknown setting: {name}")
        values[name] = _coerce(name, value, known[name])
    return Settings(**values)


def _coerce(name, value, expected):
    if expected is str:
        if not isinstance(value, str):
            raise ConfigError(f"setting {name} must be text")
        return value
    value = number(value, f"setting {name}")
    if value < 0:
        raise ConfigError(f"setting {name} must not be negative")
    if expected is int:
        if value != int(value):
            raise ConfigError(f"setting {name} must be a whole number")
        return int(value)
    return value
