"""What a shipment costs, line by line, as quoted and as stored."""
from dataclasses import dataclass

BASE = "base"
FUEL = "fuel"


@dataclass(frozen=True)
class Line:
    code: str
    pence: int


@dataclass(frozen=True)
class Quote:
    service: str
    zone: int
    billable_grams: int
    lines: tuple

    @property
    def total(self):
        return sum(line.pence for line in self.lines)

    def amount(self, code):
        return sum(line.pence for line in self.lines if line.code == code)

    @property
    def surcharge_codes(self):
        return [line.code for line in self.lines if line.code not in (BASE, FUEL)]
