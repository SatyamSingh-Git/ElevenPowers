"""When a mileage limit will be reached, at the rate the vehicle has been driven."""
from datetime import timedelta
import math

from .usage import daily_average


def projected_day(fleet, item, as_of):
    """The day `item` falls due: its date limit or the day its miles run out, if sooner.

    Returns None when neither can be said: no date limit and no driving to go on.
    """
    candidates = [item.due_date] if item.due_date is not None else []
    if item.remaining_miles is not None:
        if item.remaining_miles <= 0:
            candidates.append(as_of)
        else:
            rate = daily_average(fleet, item.vehicle_id, as_of)
            if rate:
                candidates.append(as_of + timedelta(days=math.ceil(item.remaining_miles / rate)))
    return min(candidates, default=None)
