"""Time comes from a clock object, so a run can be replayed at any moment."""
from datetime import date, datetime

from .errors import ValidationError

TIMESTAMP = "%Y-%m-%dT%H:%M"


class SystemClock:
    def now(self):
        return datetime.now().replace(second=0, microsecond=0)


class FixedClock:
    def __init__(self, at):
        self.at = at

    def now(self):
        return self.at


def parse_timestamp(text):
    try:
        return datetime.strptime(text, TIMESTAMP)
    except ValueError:
        raise ValidationError(f"invalid time: {text} (expected YYYY-MM-DDTHH:MM)") from None


def format_timestamp(moment):
    return moment.strftime(TIMESTAMP)


def parse_day(text):
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValidationError(f"invalid date: {text} (expected YYYY-MM-DD)") from None
