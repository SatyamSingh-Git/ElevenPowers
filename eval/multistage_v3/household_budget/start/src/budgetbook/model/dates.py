"""Calendar dates and budget months."""
import calendar
from dataclasses import dataclass
import datetime as dt
import re

from ..errors import ValidationError

DATE_STYLES = {
    "iso": "%Y-%m-%d",
    "dmy": "%d/%m/%Y",
    "mdy": "%m/%d/%Y",
    "iso_time": "%Y-%m-%d %H:%M:%S",
}

_MONTH = re.compile(r"(\d{4})-(\d{2})")


def parse_date(text, style="iso"):
    try:
        return dt.datetime.strptime(text.strip(), DATE_STYLES[style]).date()
    except ValueError:
        raise ValidationError(f"invalid date: {text}") from None


@dataclass(frozen=True, order=True)
class Month:
    year: int
    month: int

    @classmethod
    def parse(cls, text):
        match = _MONTH.fullmatch(text.strip())
        if not match or not 1 <= int(match.group(2)) <= 12:
            raise ValidationError(f"invalid month: {text}")
        return cls(int(match.group(1)), int(match.group(2)))

    @classmethod
    def of(cls, day):
        return cls(day.year, day.month)

    @property
    def first_day(self):
        return dt.date(self.year, self.month, 1)

    @property
    def last_day(self):
        return dt.date(self.year, self.month, calendar.monthrange(self.year, self.month)[1])

    def day(self, number):
        """Day `number` of this month, or its last day when the month is shorter."""
        return dt.date(self.year, self.month, min(number, self.last_day.day))

    def next(self):
        return Month(self.year + self.month // 12, self.month % 12 + 1)

    def previous(self):
        return Month(self.year - (self.month == 1), (self.month - 2) % 12 + 1)

    def __contains__(self, day):
        return (day.year, day.month) == (self.year, self.month)

    def __str__(self):
        return f"{self.year:04d}-{self.month:02d}"


def months_of_year(year):
    return [Month(year, number) for number in range(1, 13)]


def months_between(first, last):
    """Every month from the one holding `first` to the one holding `last`, both included."""
    month, end = Month.of(first), Month.of(last)
    while month <= end:
        yield month
        month = month.next()
