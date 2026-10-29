"""Attendance over a period: how often patients came, per practitioner."""
from dataclasses import dataclass

from ..model.booking import ATTENDED, NO_SHOW
from .textfmt import percent, table


@dataclass(frozen=True)
class Attendance:
    practitioner: str
    attended: int
    missed: int

    @property
    def rate(self):
        """Share of finished appointments the patient came to, as a percentage."""
        finished = self.attended + self.missed
        return 100 * self.attended / finished if finished else 0.0


def attendance(bookings, clinic, first, last):
    """One line per practitioner for appointments from `first` to `last` inclusive."""
    found = []
    for practitioner in clinic.practitioners:
        theirs = [b for b in bookings if b.practitioner == practitioner.id and first <= b.day <= last]
        found.append(Attendance(
            practitioner.name,
            sum(1 for b in theirs if b.status == ATTENDED),
            sum(1 for b in theirs if b.status == NO_SHOW),
        ))
    return found


def render_attendance(lines, first, last):
    rows = [[line.practitioner, line.attended, line.missed, percent(line.rate)] for line in lines]
    return [f"Attendance {first} to {last}"] + table(["practitioner", "came", "missed", "rate"], rows)
