"""The due list: every service of every vehicle, most urgent first."""
from ..services.scheduling import due_items


def due_rows(fleet, as_of, vehicle_id=None):
    return [(item.vehicle_id, item.code, item.service, item.due_miles, item.remaining_miles,
             item.due_date, item.remaining_days, item.status)
            for item in due_items(fleet, as_of, vehicle_id)]
