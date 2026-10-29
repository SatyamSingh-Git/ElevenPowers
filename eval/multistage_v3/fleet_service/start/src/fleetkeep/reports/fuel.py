"""Fuel bought and fuel economy over a period.

Economy uses the full-tank method: the miles between the first and last
fill-ups that logged an odometer, over the gallons bought at every logged
fill-up after the first. A vehicle with fewer than two logged fill-ups has no
economy figure.
"""
from decimal import Decimal, ROUND_HALF_UP

from ..model.money import dollars

MPG_PLACES = Decimal("0.1")


def _economy(fills):
    logged = sorted((e for e in fills if e.odometer is not None), key=lambda e: (e.day, e.odometer))
    if len(logged) < 2:
        return None, None
    miles = logged[-1].odometer - logged[0].odometer
    burned = sum((e.gallons for e in logged[1:]), Decimal(0))
    return miles, (Decimal(miles) / burned).quantize(MPG_PLACES, rounding=ROUND_HALF_UP)


def fuel_rows(fleet, period):
    rows = []
    for vehicle in fleet.vehicles():
        fills = [entry for entry in fleet.fuel(vehicle.id) if entry.day in period]
        if not fills:
            continue
        gallons = sum((entry.gallons for entry in fills), Decimal(0))
        cost = sum(entry.cost for entry in fills)
        miles, mpg = _economy(fills)
        rows.append((vehicle.id, len(fills), gallons, dollars(cost), miles, mpg))
    return rows
