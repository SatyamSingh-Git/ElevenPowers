"""The weekly view: each zone and kind's daily mean over the seven days ending on a day."""
from datetime import timedelta

from .formatting import heading, number, table

DAYS = 7


def week_days(last_day):
    return [last_day - timedelta(days=offset) for offset in range(DAYS - 1, -1, -1)]


def weekly_table(last_day, stats_by_day):
    """``stats_by_day`` maps each day to its DailyStats; days without readings show ``-``."""
    days = week_days(last_day)
    means = {}
    units = {}
    for day in days:
        for stats in stats_by_day.get(day, []):
            means[(stats.zone, stats.kind, day)] = stats.mean
            units[(stats.zone, stats.kind)] = stats.unit
    title = heading(f"Week ending {last_day.isoformat()}")
    if not units:
        return f"{title}\nno readings"
    rows = [
        [zone, kind, unit, *(number(kind, means.get((zone, kind, day))) for day in days)]
        for (zone, kind), unit in sorted(units.items())
    ]
    return f"{title}\n" + table(["zone", "kind", "unit", *(day.strftime("%a %d") for day in days)], rows)
