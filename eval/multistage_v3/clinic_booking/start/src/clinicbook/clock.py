"""Clocks. Anything that needs the current time is handed a clock, so runs can be replayed."""
from datetime import datetime


class FixedClock:
    """A clock stopped at one moment. `advance` moves it on."""

    def __init__(self, moment):
        self.moment = moment

    def now(self):
        return self.moment

    def advance(self, delta):
        self.moment += delta


class SystemClock:
    """The machine's local time, to the minute."""

    def now(self):
        return datetime.now().replace(second=0, microsecond=0)
