"""How far vehicles travel, from their odometer readings."""
from datetime import timedelta


def miles_in_period(fleet, vehicle_id, period):
    """Miles between the last reading before the period and the last reading in it."""
    before = fleet.odometer_on(vehicle_id, period.start - timedelta(days=1))
    return fleet.odometer_on(vehicle_id, period.end) - before


def daily_average(fleet, vehicle_id, as_of):
    """Average miles a day since the vehicle entered service, or None before its first day."""
    vehicle = fleet.vehicle(vehicle_id)
    days = (as_of - vehicle.in_service).days
    if days <= 0:
        return None
    return (fleet.odometer_on(vehicle_id, as_of) - vehicle.start_odometer) / days
