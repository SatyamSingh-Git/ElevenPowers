"""Clocks, and the minute-precision timestamps used across the box office."""
from datetime import datetime

TIME_FORMAT = "%Y-%m-%dT%H:%M"


def parse_time(text):
    try:
        return datetime.strptime(text.strip(), TIME_FORMAT)
    except ValueError:
        raise ValueError(f"expected a time like 2026-04-12T19:30, got {text!r}") from None


def format_time(moment):
    return moment.strftime(TIME_FORMAT)


class FixedClock:
    """A clock that only moves when told to. The command line's --now uses one."""

    def __init__(self, moment):
        self._moment = moment

    def now(self):
        return self._moment

    def set(self, moment):
        self._moment = moment


class SystemClock:
    def now(self):
        return datetime.now().replace(second=0, microsecond=0)
