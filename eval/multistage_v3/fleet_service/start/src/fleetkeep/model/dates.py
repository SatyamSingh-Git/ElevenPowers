"""Calendar helpers: parsing, month arithmetic and inclusive periods."""
import calendar
from dataclasses import dataclass
from datetime import date, timedelta

from ..errors import FleetError


def parse_date(text):
    try:
        return date.fromisoformat(text.strip())
    except ValueError:
        raise FleetError("E142", text=text) from None


def add_months(start, months):
    """The same day `months` later, or the month's last day when it is shorter."""
    index = start.month - 1 + months
    year, month = start.year + index // 12, index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@dataclass(frozen=True)
class Period:
    """A run of whole days; both `start` and `end` are part of it."""

    start: date
    end: date

    def __post_init__(self):
        if self.end < self.start:
            raise FleetError("E144", start=self.start.isoformat(), end=self.end.isoformat())

    @property
    def days(self):
        return (self.end - self.start).days + 1

    def __contains__(self, day):
        return self.start <= day <= self.end

    def each_day(self):
        day = self.start
        while day <= self.end:
            yield day
            day += timedelta(days=1)
