"""Days vehicles spend in the shop.

A work order keeps its vehicle out of service from the day it opens up to the
day before it closes, so a vehicle back on the road the same day loses no day.
An order still open counts to the end of the period. Overlapping orders on one
vehicle count each day once. Breakdown days are the days lost to orders opened
for a breakdown rather than for planned work.
"""
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP


def days_down(fleet, vehicle_id, period, breakdowns_only=False):
    down = set()
    for order in fleet.orders(vehicle_id):
        if breakdowns_only and not order.breakdown:
            continue
        last = order.closed - timedelta(days=1) if order.closed else period.end
        down.update(day for day in period.each_day() if order.opened <= day <= last)
    return len(down)


def orders_in(fleet, vehicle_id, period):
    """Work orders that kept the vehicle in the shop for part of the period."""
    return [order for order in fleet.orders(vehicle_id)
            if order.opened <= period.end and (order.closed is None or order.closed > period.start)]


def availability(fleet, vehicle_id, period):
    """Percentage of the period's days the vehicle was available, to one decimal."""
    up = period.days - days_down(fleet, vehicle_id, period)
    return (Decimal(100 * up) / period.days).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
