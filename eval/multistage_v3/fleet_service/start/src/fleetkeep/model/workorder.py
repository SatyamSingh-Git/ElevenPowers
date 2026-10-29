"""Work orders, the parts and labour charged to them, and the services they record."""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

from ..errors import FleetError
from .money import times

MAX_LABOUR_HOURS = Decimal("24")


def parse_hours(text):
    try:
        hours = Decimal(text.strip())
    except InvalidOperation:
        raise FleetError("E143", text=text) from None
    if not hours.is_finite() or not 0 < hours <= MAX_LABOUR_HOURS:
        raise FleetError("E143", text=text)
    return hours.quantize(Decimal("0.01"))


@dataclass(frozen=True)
class PartLine:
    number: str
    description: str
    quantity: int
    unit_price: int

    @property
    def amount(self):
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class LabourLine:
    mechanic: str
    hours: Decimal
    rate: int

    @property
    def amount(self):
        return times(self.rate, self.hours)


@dataclass
class WorkOrder:
    id: str
    vehicle_id: str
    opened: date
    services: tuple = ()
    note: str = ""
    breakdown: bool = False
    closed: date | None = None
    parts: list = field(default_factory=list)
    labour: list = field(default_factory=list)

    @property
    def is_open(self):
        return self.closed is None

    @property
    def status(self):
        return "open" if self.is_open else "closed"

    @property
    def parts_total(self):
        return sum(line.amount for line in self.parts)

    @property
    def labour_total(self):
        return sum(line.amount for line in self.labour)

    def add_line(self, line):
        if not self.is_open:
            raise FleetError("E122", order=self.id)
        if isinstance(line, PartLine):
            self.parts.append(line)
        else:
            self.labour.append(line)

    def close(self, day):
        if day < self.opened:
            raise FleetError("E123", order=self.id, opened=self.opened.isoformat())
        self.closed = day


@dataclass(frozen=True)
class ServiceRecord:
    vehicle_id: str
    code: str
    day: date
    odometer: int
    order_id: str = ""
