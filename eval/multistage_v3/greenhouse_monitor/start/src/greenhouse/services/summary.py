"""Daily statistics per zone and sensor kind."""
from collections import defaultdict
from statistics import fmean

from ..core.model import DailyStats
from ..core.units import round_for


def summarize(readings):
    """Count, lowest, highest and mean value for each zone and kind, sorted by zone then kind."""
    values = defaultdict(list)
    units = {}
    for item in readings:
        values[(item.zone, item.kind)].append(item.value)
        units[(item.zone, item.kind)] = item.unit
    return [
        DailyStats(
            zone=zone,
            kind=kind,
            unit=units[(zone, kind)],
            count=len(numbers),
            low=min(numbers),
            high=max(numbers),
            mean=round_for(kind, fmean(numbers)),
        )
        for (zone, kind), numbers in sorted(values.items())
    ]


def hourly_means(readings):
    """Mean value per (zone, kind, hour), the hour as a datetime on the hour."""
    values = defaultdict(list)
    for item in readings:
        hour = item.at.replace(minute=0, second=0)
        values[(item.zone, item.kind, hour)].append(item.value)
    return {key: fmean(numbers) for key, numbers in sorted(values.items())}


def mean_changes(today, previous):
    """How far each zone and kind's mean moved since the previous day's statistics."""
    before = {(stats.zone, stats.kind): stats.mean for stats in previous}
    return {
        (stats.zone, stats.kind): round_for(stats.kind, stats.mean - before[(stats.zone, stats.kind)])
        for stats in today
        if (stats.zone, stats.kind) in before
    }
