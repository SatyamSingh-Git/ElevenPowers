"""Housekeeping checks: records that look forgotten or wrong.

Each check takes the fleet and the day to check as of, and yields findings.
"""
from dataclasses import dataclass
from datetime import timedelta

from .inspections import latest_treads

STALE_ORDER_DAYS = 14
READING_GAP_DAYS = 30
MIN_TREAD_32NDS = 4


@dataclass(frozen=True)
class Finding:
    subject: str
    text: str


def stale_orders(fleet, as_of):
    for order in fleet.orders():
        days = (as_of - order.opened).days
        if order.is_open and days > STALE_ORDER_DAYS:
            yield Finding(order.id, f"open for {days} days on {order.vehicle_id}")


def reading_gaps(fleet, as_of):
    for vehicle in fleet.active_vehicles(as_of):
        readings = [r for r in fleet.readings(vehicle.id) if r.day <= as_of]
        since = readings[-1].day if readings else vehicle.in_service
        if (as_of - since).days > READING_GAP_DAYS:
            yield Finding(vehicle.id, f"no odometer reading since {since.isoformat()}")


def fill_up_odometers(fleet, as_of):
    """Fill-ups logged at an odometer below one the vehicle had already shown."""
    for entry in fleet.fuel():
        if entry.odometer is None or entry.day > as_of:
            continue
        known = fleet.odometer_on(entry.vehicle_id, entry.day - timedelta(days=1))
        if entry.odometer < known:
            yield Finding(entry.vehicle_id, f"fill-up on {entry.day.isoformat()} logged "
                                            f"odometer {entry.odometer}, below {known}")


def empty_stock(fleet, as_of):
    for item in fleet.stock():
        if item.on_hand == 0:
            yield Finding(item.number, "out of stock")


def grounded_vehicles(fleet, as_of):
    for defect in fleet.defects():
        if defect.grounds_vehicle and defect.reported <= as_of:
            yield Finding(defect.vehicle_id, f"out of service: {defect.id} {defect.description}")


def worn_tyres(fleet, as_of):
    for vehicle in fleet.active_vehicles(as_of):
        for reading in latest_treads(fleet, vehicle.id, as_of):
            if reading.depth < MIN_TREAD_32NDS:
                yield Finding(vehicle.id, f"{reading.position} tread at {reading.depth}/32")


CHECKS = (stale_orders, reading_gaps, fill_up_odometers, empty_stock, grounded_vehicles,
          worn_tyres)


def run_checks(fleet, as_of):
    return [finding for check in CHECKS for finding in check(fleet, as_of)]
