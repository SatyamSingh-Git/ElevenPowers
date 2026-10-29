"""Settings from `payroll.ini` in the data directory, with defaults for anything left out."""
import configparser
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from payroll.errors import PayrollError
from payroll.model.period import PayCalendar

SETTINGS_FILE = "payroll.ini"

DEFAULTS = {
    "company": {
        "name": "Example Co",
        "pay_frequency": "weekly",
        "first_period_start": "2026-01-05",
        "pay_delay_days": "3",
    },
    "overtime": {
        "daily_threshold": "8",
        "multiplier": "1.5",
        "holiday_multiplier": "2.0",
    },
    "timesheet": {
        "max_hours_per_day": "24",
    },
}


@dataclass(frozen=True)
class Settings:
    company_name: str
    pay_frequency: str
    first_period_start: date
    pay_delay_days: int
    daily_threshold: Decimal
    overtime_multiplier: Decimal
    holiday_multiplier: Decimal
    max_hours_per_day: Decimal

    def calendar(self):
        return PayCalendar(self.pay_frequency, self.first_period_start, self.pay_delay_days)


def load_settings(data_dir):
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_dict(DEFAULTS)
    path = Path(data_dir) / SETTINGS_FILE
    if path.exists():
        try:
            parser.read(path, encoding="utf-8")
        except configparser.Error as error:
            raise PayrollError(f"{SETTINGS_FILE}: {error.message}") from None
    _reject_unknown(parser)
    settings = Settings(
        company_name=parser.get("company", "name").strip(),
        pay_frequency=parser.get("company", "pay_frequency").strip(),
        first_period_start=_date(parser, "company", "first_period_start"),
        pay_delay_days=_whole(parser, "company", "pay_delay_days"),
        daily_threshold=_positive(parser, "overtime", "daily_threshold"),
        overtime_multiplier=_multiplier(parser, "overtime", "multiplier"),
        holiday_multiplier=_multiplier(parser, "overtime", "holiday_multiplier"),
        max_hours_per_day=_positive(parser, "timesheet", "max_hours_per_day"),
    )
    # Building the calendar rejects an unknown pay frequency now rather than at the first pay run.
    settings.calendar()
    return settings


def _reject_unknown(parser):
    for section in parser.sections():
        if section not in DEFAULTS:
            raise PayrollError(f"unknown setting section [{section}]")
        for key in parser[section]:
            if key not in DEFAULTS[section]:
                raise PayrollError(f"unknown setting {section}.{key}")


def _bad(section, key, value):
    return PayrollError(f"bad setting {section}.{key}: {value}")


def _decimal(parser, section, key):
    value = parser.get(section, key).strip()
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise _bad(section, key, value) from None
    if not number.is_finite():
        raise _bad(section, key, value)
    return number


def _positive(parser, section, key):
    number = _decimal(parser, section, key)
    if number <= 0:
        raise _bad(section, key, number)
    return number


def _multiplier(parser, section, key):
    number = _decimal(parser, section, key)
    if number < 1:
        raise _bad(section, key, number)
    return number


def _whole(parser, section, key):
    value = parser.get(section, key).strip()
    if not value.isdigit():
        raise _bad(section, key, value)
    return int(value)


def _date(parser, section, key):
    value = parser.get(section, key).strip()
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise _bad(section, key, value) from None
