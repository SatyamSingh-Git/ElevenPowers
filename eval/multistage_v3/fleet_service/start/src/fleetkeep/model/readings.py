"""Odometer readings and fill-ups."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from ..errors import FleetError

MAX_FILL_GALLONS = Decimal("150")
GALLON_PLACES = Decimal("0.001")


def parse_gallons(text):
    try:
        gallons = Decimal(text.strip())
    except InvalidOperation:
        raise FleetError("E143", text=text) from None
    if not gallons.is_finite():
        raise FleetError("E143", text=text)
    return gallons.quantize(GALLON_PLACES)


def parse_odometer(text):
    try:
        value = int(text.strip().replace(",", ""))
    except ValueError:
        raise FleetError("E143", text=text) from None
    if value < 0:
        raise FleetError("E143", text=text)
    return value


@dataclass(frozen=True)
class OdometerReading:
    vehicle_id: str
    day: date
    odometer: int


@dataclass(frozen=True)
class FuelEntry:
    vehicle_id: str
    day: date
    gallons: Decimal
    cost: int
    odometer: int | None = None

    def __post_init__(self):
        if self.gallons <= 0:
            raise FleetError("E111", gallons=self.gallons)
        if self.gallons > MAX_FILL_GALLONS:
            raise FleetError("E112", gallons=self.gallons, limit=MAX_FILL_GALLONS)

    def same_purchase(self, other):
        """True for the same fill-up exported twice by a fuel-card provider."""
        return (self.vehicle_id, self.day, self.gallons, self.cost) == (
            other.vehicle_id, other.day, other.gallons, other.cost)
