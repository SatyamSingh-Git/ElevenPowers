"""The term calendar: which date each term day falls on.

Term days count school days only: Monday to Friday, skipping the days off
the calendar file lists. Day 1 is the first school day on or after `start`.
Everything else in the gradebook works in term days; the calendar is only
for showing dates to people.
"""
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from ..errors import ConfigError

# Enough for any school term; stops a bad calendar from looping for ever.
MAX_TERM_DAYS = 400


@dataclass(frozen=True)
class TermCalendar:
    start: date
    days_off: frozenset

    def is_school_day(self, when):
        return when.weekday() < 5 and when not in self.days_off

    def date_of(self, day):
        if day < 1 or day > MAX_TERM_DAYS:
            raise ConfigError(f"term day {day} is outside 1 to {MAX_TERM_DAYS}")
        when, counted = self.start, 0
        while True:
            if self.is_school_day(when):
                counted += 1
                if counted == day:
                    return when
            when += timedelta(days=1)

    def day_of(self, when):
        """The term day `when` falls on; a weekend or day off counts as the next school day."""
        if when < self.start:
            raise ConfigError(f"{when.isoformat()} is before the term starts")
        day, cursor = 0, self.start
        while cursor <= when:
            if self.is_school_day(cursor):
                day += 1
            cursor += timedelta(days=1)
        if not self.is_school_day(when):
            day += 1
        if day > MAX_TERM_DAYS:
            raise ConfigError(f"{when.isoformat()} is past the end of any term")
        return day


def load_calendar(path):
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    try:
        start = date.fromisoformat(raw["start"])
        days_off = frozenset(date.fromisoformat(text) for text in raw.get("days_off", []))
    except (KeyError, ValueError) as error:
        raise ConfigError(f"{path.name}: calendar needs a start date and ISO dates ({error})") from None
    return TermCalendar(start, days_off)
