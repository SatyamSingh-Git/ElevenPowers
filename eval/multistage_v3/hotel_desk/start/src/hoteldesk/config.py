"""Hotel settings, read from an optional JSON file (`hotel.json` by default).

Any setting the file leaves out keeps its default. Money is written as an
amount ("25.00") and times of day as "HH:MM".
"""
from dataclasses import dataclass
from datetime import time
import json
from pathlib import Path

from .dates import parse_time
from .errors import ValidationError
from .money import parse_money


@dataclass(frozen=True)
class Settings:
    check_in_time: time = time(15, 0)
    check_out_time: time = time(11, 0)
    max_stay_nights: int = 30
    weekend_uplift_percent: int = 10
    late_checkout_fee: int = 2500
    journal_file: str = "audit_journal.csv"
    currency: str = "USD"


def _count(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"Not a whole number: {value}")
    return value


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"Not a name: {value}")
    return value.strip()


_READERS = {
    "check_in_time": parse_time,
    "check_out_time": parse_time,
    "max_stay_nights": _count,
    "weekend_uplift_percent": _count,
    "late_checkout_fee": parse_money,
    "journal_file": _text,
    "currency": _text,
}


def load_settings(path=None):
    """The settings in `path`, or the defaults when there is no such file."""
    if path is None or not Path(path).is_file():
        return Settings()
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValidationError(f"{path} is not valid JSON: {error}") from None
    values = {}
    for key, raw in data.items():
        if key not in _READERS:
            raise ValidationError(f"Unknown setting: {key}")
        values[key] = _READERS[key](raw)
    return Settings(**values)
