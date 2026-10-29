"""Bookings and their statuses."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from .times import add_minutes

BOOKED = "booked"
ATTENDED = "attended"
NO_SHOW = "no_show"
CANCELLED = "cancelled"
STATUSES = (BOOKED, ATTENDED, NO_SHOW, CANCELLED)


@dataclass
class Booking:
    id: str
    patient: str
    phone: str
    practitioner: str
    room: str
    day: date
    start: time
    minutes: int
    status: str = BOOKED
    created: datetime | None = None

    @property
    def end(self):
        return add_minutes(self.start, self.minutes)

    @property
    def starts_at(self):
        return datetime.combine(self.day, self.start)

    @property
    def ends_at(self):
        return self.starts_at + timedelta(minutes=self.minutes)

    @property
    def active(self):
        """Whether the booking still holds its time with the practitioner and the room."""
        return self.status != CANCELLED

    def overlaps(self, day, start, minutes):
        """Whether this booking, if still active, shares any minute with the given span."""
        if not self.active or day != self.day:
            return False
        other_start = datetime.combine(day, start)
        other_end = other_start + timedelta(minutes=minutes)
        return other_start < self.ends_at and self.starts_at < other_end
