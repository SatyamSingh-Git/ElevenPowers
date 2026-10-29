"""Time handling.

Nothing in the package reads the wall clock. Commands are given a Clock, and
the command line builds one from ``--now`` so a scheduled run and a re-run of
an old day behave the same way.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from .errors import ValidationError

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"


class Clock(Protocol):
    def now(self) -> datetime:
        ...


@dataclass
class FixedClock:
    """A clock that reads whatever time it was set to."""

    at: datetime

    def now(self) -> datetime:
        return self.at


def parse_timestamp(text: str) -> datetime:
    """Parse ``YYYY-MM-DDTHH:MM:SS`` local greenhouse time."""
    try:
        value = datetime.fromisoformat(text.strip())
    except ValueError:
        raise ValidationError(f"bad time: {text.strip()}") from None
    if value.tzinfo is not None:
        raise ValidationError(f"bad time: {text.strip()}")
    return value.replace(microsecond=0)


def format_timestamp(value: datetime) -> str:
    return value.strftime(TIMESTAMP_FORMAT)


def parse_day(text: str) -> date:
    try:
        return date.fromisoformat(text.strip())
    except ValueError:
        raise ValidationError(f"invalid date: {text.strip()}") from None


def parse_time_of_day(text: str) -> tuple[int, int]:
    """Parse ``HH:MM`` into (hour, minute)."""
    hour, _, minute = text.strip().partition(":")
    if not (hour.isdigit() and minute.isdigit() and len(minute) == 2):
        raise ValidationError(f"invalid time of day: {text.strip()}")
    if int(hour) > 23 or int(minute) > 59:
        raise ValidationError(f"invalid time of day: {text.strip()}")
    return int(hour), int(minute)
