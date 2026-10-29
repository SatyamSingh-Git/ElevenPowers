"""Text sparklines of a zone's hourly means over one day.

Each of the 24 characters is one hour, from a space for the day's lowest
mean to ``#`` for its highest; an hour without readings shows ``.``.
"""
from .formatting import label, number

LEVELS = " _-=+*#"
NO_DATA = "."


def sparkline(values):
    """One character per value; None is an hour without readings."""
    present = [value for value in values if value is not None]
    if not present:
        return NO_DATA * len(values)
    low, high = min(present), max(present)
    span = high - low
    marks = []
    for value in values:
        if value is None:
            marks.append(NO_DATA)
        elif span == 0:
            marks.append(LEVELS[len(LEVELS) // 2])
        else:
            marks.append(LEVELS[round((value - low) / span * (len(LEVELS) - 1))])
    return "".join(marks)


def day_chart(hourly, zone, kind):
    """The chart line for one zone and kind from ``hourly_means`` output, or None without data."""
    by_hour = {hour.hour: mean for (z, k, hour), mean in hourly.items() if z == zone and k == kind}
    if not by_hour:
        return None
    values = [by_hour.get(hour) for hour in range(24)]
    low, high = min(by_hour.values()), max(by_hour.values())
    return f"{zone} {label(kind)}  |{sparkline(values)}|  {number(kind, low)} to {number(kind, high)}"
