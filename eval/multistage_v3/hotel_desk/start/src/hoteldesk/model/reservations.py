"""A reservation and the states it moves through."""
from dataclasses import dataclass
from datetime import date, datetime

BOOKED = "booked"
IN_HOUSE = "in_house"
CHECKED_OUT = "checked_out"
CANCELLED = "cancelled"
NO_SHOW = "no_show"

# Reservations in these states hold a room for every night they cover.
HOLDING = (BOOKED, IN_HOUSE)


@dataclass
class Reservation:
    id: str
    guest: str
    room_type: str
    arrival: date
    departure: date
    adults: int
    rate_plan: str
    rates: list
    status: str = BOOKED
    room: str | None = None
    source: str = "desk"
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    cancelled_on: date | None = None

    @property
    def nights(self):
        return (self.departure - self.arrival).days

    def covers(self, day):
        return self.arrival <= day < self.departure

    def rate_for(self, day):
        return self.rates[(day - self.arrival).days]

    @property
    def room_total(self):
        return sum(self.rates)
