"""Turning command-line words into dates and times."""
from datetime import date, datetime, timedelta

from ..errors import ClinicError
from ..model.hours import WEEKDAYS
from ..model.times import parse_hhmm

FULL_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


class UsageError(ClinicError):
    """A command-line value that cannot be understood."""


def parse_day(text, today):
    """`2026-03-02`, `today`, `tomorrow`, or a weekday name meaning the next one on or after today."""
    word = text.strip().lower()
    if word == "today":
        return today
    if word == "tomorrow":
        return today + timedelta(days=1)
    if word in WEEKDAYS or word in FULL_WEEKDAYS:
        ahead = (WEEKDAYS.index(word[:3]) - today.weekday()) % 7
        return today + timedelta(days=ahead)
    try:
        return date.fromisoformat(word)
    except ValueError:
        raise UsageError(f"not a day: {text}") from None


def parse_time(text):
    try:
        return parse_hhmm(text.strip())
    except ValueError:
        raise UsageError(f"not a time: {text}") from None


def parse_moment(text):
    """The `--now` option: `2026-03-02T08:30`."""
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        raise UsageError(f"not a date and time: {text}") from None


def positive(text):
    if not text.isdigit() or int(text) == 0:
        raise UsageError(f"not a positive whole number: {text}")
    return int(text)
