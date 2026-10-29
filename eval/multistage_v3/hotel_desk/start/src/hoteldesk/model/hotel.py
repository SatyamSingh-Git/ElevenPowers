"""The hotel as the desk sees it on one business date."""
from dataclasses import dataclass, field
from datetime import date

from ..errors import NotFound


@dataclass
class Hotel:
    name: str
    business_date: date
    room_types: dict
    rooms: dict
    rate_plans: dict
    reservations: dict = field(default_factory=dict)
    folios: dict = field(default_factory=dict)
    guests: dict = field(default_factory=dict)
    wake_up_calls: list = field(default_factory=list)
    lost_items: list = field(default_factory=list)

    def room_type(self, code):
        try:
            return self.room_types[code]
        except KeyError:
            raise NotFound(f"Unknown room type: {code}") from None

    def room(self, number):
        try:
            return self.rooms[number]
        except KeyError:
            raise NotFound(f"Unknown room: {number}") from None

    def rate_plan(self, code):
        try:
            return self.rate_plans[code]
        except KeyError:
            raise NotFound(f"Unknown rate plan: {code}") from None

    def reservation(self, reservation_id):
        try:
            return self.reservations[reservation_id]
        except KeyError:
            raise NotFound(f"No reservation {reservation_id}") from None

    def folio(self, reservation_id):
        try:
            return self.folios[reservation_id]
        except KeyError:
            raise NotFound(f"No folio for {reservation_id}") from None

    def guest(self, name):
        try:
            return self.guests[name]
        except KeyError:
            raise NotFound(f"No guest profile for {name}") from None

    def rooms_of_type(self, code):
        return sorted((room for room in self.rooms.values() if room.type_code == code),
                      key=lambda room: room.number)

    def reservations_with(self, *statuses):
        return [reservation for reservation in self.reservations.values() if reservation.status in statuses]
