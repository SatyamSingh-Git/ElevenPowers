"""Opening hours: a weekly pattern, public holidays and one-off closures."""
from datetime import date, timedelta

from .._generated import PUBLIC_HOLIDAYS
from .times import minutes_between, parse_hhmm

WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def weekday_name(day):
    return WEEKDAYS[day.weekday()]


def parse_window(text):
    """`09:00-17:00` as an (open, close) pair."""
    opens, sep, closes = text.partition("-")
    if not sep:
        raise ValueError(f"opening hours must look like 09:00-17:00, not {text!r}")
    window = parse_hhmm(opens.strip()), parse_hhmm(closes.strip())
    if window[0] >= window[1]:
        raise ValueError(f"opening hours close before they open: {text!r}")
    return window


class OpeningHours:
    """When the clinic is open. A day is closed if its weekday has no hours,
    if it is a public holiday, or if the clinic listed it as a closure."""

    def __init__(self, weekly, closures=(), holidays=None):
        self.weekly = {name: weekly.get(name) for name in WEEKDAYS}
        self.closures = frozenset(closures)
        if holidays is None:
            holidays = {date.fromisoformat(day): name for day, name in PUBLIC_HOLIDAYS.items()}
        self.holidays = dict(holidays)

    @classmethod
    def from_spec(cls, spec, closures=()):
        """Hours as the clinic file writes them: {"mon": "09:00-17:00", "sun": null}."""
        unknown = sorted(set(spec) - set(WEEKDAYS))
        if unknown:
            raise ValueError(f"unknown weekday in hours: {unknown[0]}")
        weekly = {name: parse_window(text) for name, text in spec.items() if text}
        return cls(weekly, closures)

    def closed_reason(self, day):
        """Why the clinic is shut on `day`, or None when it is open."""
        if day in self.holidays:
            return self.holidays[day]
        if day in self.closures:
            return "closed"
        if self.weekly[weekday_name(day)] is None:
            return f"closed on {day:%A}s"
        return None

    def window(self, day):
        """(open, close) on `day`, or None when the clinic is shut."""
        if self.closed_reason(day) is not None:
            return None
        return self.weekly[weekday_name(day)]

    def next_open_day(self, day, within=366):
        """The first day on or after `day` the clinic opens, or None if it stays shut."""
        for offset in range(within):
            candidate = day + timedelta(days=offset)
            if self.window(candidate) is not None:
                return candidate
        return None

    def open_minutes(self, day):
        window = self.window(day)
        return minutes_between(*window) if window else 0

    def describe(self):
        """One line per weekday, the way reception reads them out."""
        lines = []
        for name in WEEKDAYS:
            window = self.weekly[name]
            if window is None:
                lines.append(f"{name}  closed")
            else:
                lines.append(f"{name}  {window[0]:%H:%M}-{window[1]:%H:%M}")
        return lines
