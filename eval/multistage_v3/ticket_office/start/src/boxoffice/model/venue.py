"""The venue: named sections of lettered rows of numbered seats."""
from dataclasses import dataclass, field

from .._generated import ACCESSIBILITY_CODES


@dataclass(frozen=True)
class Seat:
    id: str
    section: str
    row: str
    number: int
    tier: str
    flags: frozenset = frozenset()

    def describe(self):
        text = f"{self.section} row {self.row} seat {self.number}"
        if self.flags:
            notes = ", ".join(ACCESSIBILITY_CODES[flag] for flag in sorted(self.flags))
            text += f" ({notes})"
        return text


@dataclass
class Section:
    name: str
    tier: str
    rows: dict = field(default_factory=dict)

    @property
    def capacity(self):
        return sum(len(seats) for seats in self.rows.values())

    def seats(self):
        for seats in self.rows.values():
            yield from seats


@dataclass
class Venue:
    name: str
    sections: list = field(default_factory=list)
    _by_id: dict = field(default_factory=dict, repr=False)

    def add_section(self, name, tier):
        section = Section(name, tier)
        self.sections.append(section)
        return section

    def add_row(self, section, row, numbers, flags):
        """Seats `numbers` of `row`; `flags` maps a seat number to its access codes."""
        seats = [Seat(f"{row}{number}", section.name, row, number, section.tier,
                      frozenset(flags.get(number, ())))
                 for number in numbers]
        section.rows[row] = seats
        for seat in seats:
            self._by_id[seat.id] = seat
        return seats

    def seat(self, seat_id):
        return self._by_id.get(seat_id)

    def seats(self):
        for section in self.sections:
            yield from section.seats()

    def section(self, name):
        for section in self.sections:
            if section.name.lower() == name.lower():
                return section
        return None

    def has_row(self, row):
        return any(row in section.rows for section in self.sections)

    def tiers(self):
        return sorted({section.tier for section in self.sections})

    @property
    def capacity(self):
        return sum(section.capacity for section in self.sections)

    def seat_order(self):
        """Each seat id's position on the seat map, for putting seats in plan order."""
        return {seat.id: index for index, seat in enumerate(self.seats())}
