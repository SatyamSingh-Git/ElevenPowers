"""Daily light per zone: the daily light integral (DLI) and the photoperiod.

Light sensors report illuminance in lux, but plants respond to photon flux.
Each hour's mean illuminance is converted with ``ppfd_per_lux`` (about 0.0185
umol/m2/s per lux for sunlight) and counted for the whole hour, so an hour
with no light reading adds nothing. The photoperiod is the number of hours
whose mean reached ``light_on_lux``.
"""
from dataclasses import dataclass

from .summary import hourly_means

LIGHT = "light"
SECONDS_PER_HOUR = 3600


@dataclass(frozen=True)
class DailyLight:
    zone: str
    dli: float
    photoperiod: int
    hours_measured: int


def daily_light(readings, settings):
    """One DailyLight per zone with light readings, sorted by zone."""
    by_zone = {}
    for (zone, kind, hour), lux in hourly_means(readings).items():
        if kind == LIGHT:
            by_zone.setdefault(zone, []).append(lux)
    return [_zone_light(zone, hours, settings) for zone, hours in sorted(by_zone.items())]


def _zone_light(zone, hours, settings):
    micromoles = sum(lux * settings.ppfd_per_lux * SECONDS_PER_HOUR for lux in hours)
    return DailyLight(
        zone=zone,
        dli=round(micromoles / 1_000_000, 2),
        photoperiod=sum(1 for lux in hours if lux >= settings.light_on_lux),
        hours_measured=len(hours),
    )
