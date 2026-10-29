"""Dates as the desk sees them: whole days, written YYYY-MM-DD."""
from datetime import date, timedelta

from ..errors import refuse


class FixedClock:
    """The library's idea of today. The desk sets it once per session."""

    def __init__(self, today):
        self._today = today

    def today(self):
        return self._today


def parse_date(text):
    try:
        return date.fromisoformat(text.strip())
    except ValueError:
        raise refuse('bad_date', text=text) from None


def format_date(day):
    return day.isoformat()


def add_days(day, days):
    return day + timedelta(days=days)


def days_late(due, day):
    """Whole days `day` is after `due`; zero or negative when not late."""
    return (day - due).days


def month_of(day):
    return f'{day.year:04d}-{day.month:02d}'
