"""Days the library is open, so nothing falls due when the doors are shut."""
from .dates import add_days

WEEKDAYS = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')


class Calendar:
    def __init__(self, closed_weekdays=(), holidays=()):
        self.closed_weekdays = frozenset(WEEKDAYS.index(name) for name in closed_weekdays)
        self.holidays = frozenset(holidays)

    def is_open(self, day):
        return day.weekday() not in self.closed_weekdays and day not in self.holidays

    def next_open_day(self, day):
        """`day` itself when the library is open then, otherwise the first open day after it."""
        while not self.is_open(day):
            day = add_days(day, 1)
        return day
