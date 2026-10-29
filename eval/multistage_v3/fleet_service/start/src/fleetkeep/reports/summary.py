"""One line per vehicle for a period: distance, running cost, economy and shop time.

Every figure is taken from the report that owns it, so the summary always
agrees with `costs`, `fuel report` and `downtime`.
"""
from .registry import PERIOD_REPORTS


def summary_rows(fleet, period):
    mpg = {row[0]: row[5] for row in PERIOD_REPORTS["fuel"](fleet, period)}
    down = {row[0]: row for row in PERIOD_REPORTS["downtime"](fleet, period)}
    rows = []
    for vehicle_id, miles, _, _, total, per_mile in PERIOD_REPORTS["costs"](fleet, period):
        _, _, days_down, _, available = down[vehicle_id]
        rows.append((vehicle_id, miles, total, per_mile, mpg.get(vehicle_id), days_down, available))
    return rows
