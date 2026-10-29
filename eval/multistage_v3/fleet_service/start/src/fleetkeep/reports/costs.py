"""What each vehicle cost to run over a period, and per mile driven.

Fuel is every fill-up in the period. Maintenance is what was charged on the
work orders closed in the period: their parts and their labour.
"""
from decimal import Decimal, ROUND_HALF_UP

from ..model.money import dollars
from ..services.usage import miles_in_period

PER_MILE_PLACES = Decimal("0.001")


def _maintenance(fleet, vehicle_id, period):
    return sum(order.parts_total + order.labour_total
               for order in fleet.orders(vehicle_id)
               if order.closed is not None and order.closed in period)


def _per_mile(cents, miles):
    if not miles:
        return None
    return (Decimal(cents) / 100 / miles).quantize(PER_MILE_PLACES, rounding=ROUND_HALF_UP)


def cost_rows(fleet, period):
    rows = []
    for vehicle in fleet.vehicles():
        miles = miles_in_period(fleet, vehicle.id, period)
        fuel = sum(entry.cost for entry in fleet.fuel(vehicle.id) if entry.day in period)
        maintenance = _maintenance(fleet, vehicle.id, period)
        total = fuel + maintenance
        rows.append((vehicle.id, miles, dollars(fuel), dollars(maintenance), dollars(total),
                     _per_mile(total, miles)))
    return rows
