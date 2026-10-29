"""Dates and times as files and the command line write them."""
from datetime import date, datetime, time, timedelta

from .errors import ValidationError


def parse_date(text):
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        raise ValidationError(f"Not a date: {text}") from None


def parse_time(text):
    try:
        return time.fromisoformat(text)
    except (TypeError, ValueError):
        raise ValidationError(f"Not a time of day: {text}") from None


def parse_timestamp(text):
    try:
        return datetime.fromisoformat(text)
    except (TypeError, ValueError):
        raise ValidationError(f"Not a timestamp: {text}") from None


def nights(start, end):
    """Each night from `start` up to, but not including, `end`."""
    return [start + timedelta(days=n) for n in range((end - start).days)]


def format_time(value):
    return value.strftime("%H:%M")
