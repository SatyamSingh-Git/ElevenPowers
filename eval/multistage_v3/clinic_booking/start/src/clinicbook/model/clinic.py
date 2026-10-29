"""The clinic as a whole: its rooms, practitioners, hours and settings."""
from dataclasses import dataclass

from ..errors import NotFound


@dataclass
class Clinic:
    name: str
    rooms: list
    practitioners: list
    hours: object
    settings: object

    def practitioner(self, practitioner_id):
        for practitioner in self.practitioners:
            if practitioner.id == practitioner_id:
                return practitioner
        raise NotFound(f"no practitioner {practitioner_id}")

    def room(self, room_id):
        for room in self.rooms:
            if room.id == room_id:
                return room
        raise NotFound(f"no room {room_id}")

    def working_on(self, day):
        """Practitioners seeing patients on `day`; nobody when the clinic is shut."""
        if self.hours.window(day) is None:
            return []
        return [practitioner for practitioner in self.practitioners if practitioner.works_on(day)]

    def practitioner_name(self, practitioner_id):
        return self.practitioner(practitioner_id).name
