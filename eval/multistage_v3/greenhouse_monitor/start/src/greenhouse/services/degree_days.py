"""Growing degree days (GDD) per zone, from each day's mean temperature.

A day adds its mean temperature minus the crop's base temperature, or nothing
when the mean is below the base. Days without a temperature mean add nothing
and are counted as missing, so a gap in the record is visible rather than
silently lowering the total.
"""
from dataclasses import dataclass

from ..config.crops import crop

TEMPERATURE = "temperature"


@dataclass(frozen=True)
class ZoneDegreeDays:
    zone: str
    crop: str
    base: float
    total: float
    days_counted: int
    days_missing: int


def degree_days(mean_temperature, base):
    return max(0.0, mean_temperature - base)


def season_degree_days(layout, stats_by_day, days):
    """GDD per zone over ``days``; ``stats_by_day`` maps a day to its DailyStats."""
    means = {
        (stats.zone, day): stats.mean
        for day, stats_list in stats_by_day.items()
        for stats in stats_list
        if stats.kind == TEMPERATURE
    }
    results = []
    for zone in layout.zones():
        base = crop(zone.crop).base_temperature
        counted = [means[(zone.id, day)] for day in days if (zone.id, day) in means]
        results.append(ZoneDegreeDays(
            zone=zone.id,
            crop=zone.crop,
            base=base,
            total=round(sum(degree_days(mean, base) for mean in counted), 1),
            days_counted=len(counted),
            days_missing=len(days) - len(counted),
        ))
    return results
