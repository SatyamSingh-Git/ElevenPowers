"""Practitioners and the rooms they work in."""
from dataclasses import dataclass

from .hours import WEEKDAYS, weekday_name


@dataclass(frozen=True)
class Room:
    id: str
    name: str
    accessible: bool = True


@dataclass(frozen=True)
class Practitioner:
    id: str
    name: str
    specialty: str
    room: str
    days: tuple = WEEKDAYS[:5]

    def works_on(self, day):
        return weekday_name(day) in self.days
