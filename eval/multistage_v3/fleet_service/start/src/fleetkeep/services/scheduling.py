"""When each vehicle's services fall due.

A service is due `interval_miles` after the odometer it was last done at, or
`interval_months` after the day it was last done, whichever comes first. A
vehicle that has never had a service counts from its start odometer and the day
it entered service.
"""
from dataclasses import dataclass
from datetime import date

from ..model.catalog import specs_for
from ..model.dates import add_months

STATUS_RANK = {"overdue": 0, "due-soon": 1, "ok": 2}


@dataclass(frozen=True)
class DueItem:
    vehicle_id: str
    code: str
    service: str
    last_day: date
    last_odometer: int
    due_miles: int | None
    remaining_miles: int | None
    due_date: date | None
    remaining_days: int | None
    status: str


def due_items(fleet, as_of, vehicle_id=None):
    """Every service of every vehicle in service (or of one vehicle), most urgent first."""
    vehicles = [fleet.vehicle(vehicle_id)] if vehicle_id else fleet.active_vehicles(as_of)
    items = []
    for vehicle in vehicles:
        odometer = fleet.odometer_on(vehicle.id, as_of)
        for spec in specs_for(vehicle.vehicle_class):
            items.append(_due_item(fleet, vehicle, spec, odometer, as_of))
    return sorted(items, key=lambda item: (STATUS_RANK[item.status], item.vehicle_id, item.code))


def _due_item(fleet, vehicle, spec, odometer, as_of):
    last = fleet.last_service(vehicle.id, spec.code)
    last_day = last.day if last else vehicle.in_service
    last_odometer = last.odometer if last else vehicle.start_odometer
    due_miles = remaining_miles = due_date = remaining_days = None
    if spec.interval_miles:
        due_miles = last_odometer + spec.interval_miles
        remaining_miles = due_miles - odometer
    if spec.interval_months:
        due_date = add_months(last_day, spec.interval_months)
        remaining_days = (due_date - as_of).days
    return DueItem(vehicle.id, spec.code, spec.name, last_day, last_odometer, due_miles,
                   remaining_miles, due_date, remaining_days,
                   classify(remaining_miles, remaining_days, fleet.settings))


def classify(remaining_miles, remaining_days, settings):
    """`overdue` once either limit has passed, `due-soon` within the warning window."""
    miles = remaining_miles if remaining_miles is not None else float("inf")
    days = remaining_days if remaining_days is not None else float("inf")
    if miles < 0 or days < 0:
        return "overdue"
    if miles <= settings.due_soon_miles or days <= settings.due_soon_days:
        return "due-soon"
    return "ok"
