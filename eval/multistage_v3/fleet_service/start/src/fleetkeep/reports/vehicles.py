"""The vehicle list and the service catalog, as reports."""
from decimal import Decimal, ROUND_HALF_UP

from ..model.catalog import specs_for
from ..model.vehicle import VEHICLE_CLASSES
from ..services.usage import daily_average


def vehicle_rows(fleet, as_of):
    rows = []
    for vehicle in fleet.vehicles():
        readings = [r for r in fleet.readings(vehicle.id) if r.day <= as_of]
        average = daily_average(fleet, vehicle.id, as_of)
        rows.append((vehicle.id, vehicle.vehicle_class, vehicle.make, vehicle.model, vehicle.year,
                     fleet.odometer_on(vehicle.id, as_of),
                     readings[-1].day if readings else None,
                     None if average is None
                     else Decimal(average).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP),
                     vehicle.retired))
    return rows


def catalog_rows(vehicle_class=None):
    classes = [vehicle_class] if vehicle_class else VEHICLE_CLASSES
    seen, rows = set(), []
    for name in classes:
        for spec in specs_for(name):
            if spec.code in seen:
                continue
            seen.add(spec.code)
            rows.append((spec.code, spec.name, spec.interval_miles or None,
                         spec.interval_months or None, ",".join(spec.classes)))
    return sorted(rows)
