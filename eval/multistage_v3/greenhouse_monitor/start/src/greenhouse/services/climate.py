"""Vapour pressure deficit (VPD) and dew point per zone.

VPD is how much more water the air could hold, in kPa: the saturation vapour
pressure at the air temperature (Tetens) times the share of it still missing.
Below ``vpd_low_kpa`` leaves barely transpire and fungal disease spreads;
above ``vpd_high_kpa`` plants close their stomata and stop growing.
"""
import math
from dataclasses import dataclass

TEMPERATURE = "temperature"
HUMIDITY = "humidity"


@dataclass(frozen=True)
class ZoneClimate:
    zone: str
    temperature: float
    humidity: float
    vpd: float
    dew_point: float
    band: str


def saturation_pressure(celsius):
    """Saturation vapour pressure in kPa at ``celsius``."""
    return 0.6108 * math.exp(17.27 * celsius / (celsius + 237.3))


def vapour_pressure_deficit(celsius, humidity):
    return saturation_pressure(celsius) * (1 - humidity / 100)


def dew_point(celsius, humidity):
    """Dew point in C by the Magnus formula; humidity in percent, above zero."""
    gamma = math.log(humidity / 100) + 17.27 * celsius / (celsius + 237.3)
    return 237.3 * gamma / (17.27 - gamma)


def band(vpd, settings):
    if vpd < settings.vpd_low_kpa:
        return "low"
    if vpd > settings.vpd_high_kpa:
        return "high"
    return "ok"


def zone_climate(stats, settings):
    """Climate per zone from daily statistics, for zones with both temperature and humidity."""
    means = {(s.zone, s.kind): s.mean for s in stats}
    zones = sorted({zone for zone, kind in means if kind == TEMPERATURE} & {zone for zone, kind in means if kind == HUMIDITY})
    climate = []
    for zone in zones:
        celsius, humidity = means[(zone, TEMPERATURE)], means[(zone, HUMIDITY)]
        vpd = vapour_pressure_deficit(celsius, humidity)
        climate.append(ZoneClimate(
            zone=zone,
            temperature=celsius,
            humidity=humidity,
            vpd=round(vpd, 2),
            dew_point=round(dew_point(celsius, max(humidity, 1.0)), 1),
            band=band(vpd, settings),
        ))
    return climate
