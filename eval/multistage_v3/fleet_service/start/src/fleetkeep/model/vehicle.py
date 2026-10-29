"""Vehicles and the rules their identifiers and details follow."""
from dataclasses import dataclass
from datetime import date
import re

from ..errors import FleetError

VEHICLE_ID = re.compile(r"^[A-Z]{2,4}-[0-9]{3,4}$")
VEHICLE_CLASSES = ("light", "medium", "heavy")
EARLIEST_MODEL_YEAR = 1980


def normalise_vehicle_id(text):
    """Vehicle ids are typed in any case and stored in upper case."""
    vehicle_id = text.strip().upper()
    if not VEHICLE_ID.match(vehicle_id):
        raise FleetError("E101", vehicle=text)
    return vehicle_id


@dataclass(frozen=True)
class Vehicle:
    id: str
    vehicle_class: str
    make: str
    model: str
    year: int
    in_service: date
    start_odometer: int = 0
    retired: date | None = None

    def __post_init__(self):
        if not VEHICLE_ID.match(self.id):
            raise FleetError("E101", vehicle=self.id)
        if self.vehicle_class not in VEHICLE_CLASSES:
            raise FleetError("E102", vehicle_class=self.vehicle_class)
        latest = self.in_service.year + 1
        if not EARLIEST_MODEL_YEAR <= self.year <= latest:
            raise FleetError("E108", year=self.year, earliest=EARLIEST_MODEL_YEAR, latest=latest)
        if self.start_odometer < 0:
            raise FleetError("E143", text=str(self.start_odometer))

    def in_service_on(self, day):
        return self.in_service <= day and (self.retired is None or day < self.retired)

    @property
    def description(self):
        return f"{self.year} {self.make} {self.model}"
