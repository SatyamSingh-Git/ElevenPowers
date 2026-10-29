"""Condensation risk: hours when a zone's air came within ``condensation_margin`` C of its dew point.

Leaves are colder than the air around them, so they reach the dew point
first. Hours with a narrow margin are when botrytis takes hold.
"""
from dataclasses import dataclass

from .climate import HUMIDITY, TEMPERATURE, dew_point
from .summary import hourly_means


@dataclass(frozen=True)
class RiskHour:
    zone: str
    hour: int
    temperature: float
    dew_point: float

    @property
    def margin(self):
        return self.temperature - self.dew_point


def risk_hours(readings, margin):
    """Hours whose mean temperature was within ``margin`` of the dew point, by zone and hour."""
    hourly = hourly_means(readings)
    risky = []
    for (zone, kind, hour), celsius in hourly.items():
        if kind != TEMPERATURE:
            continue
        humidity = hourly.get((zone, HUMIDITY, hour))
        if humidity is None or humidity <= 0:
            continue
        point = dew_point(celsius, humidity)
        if celsius - point < margin:
            risky.append(RiskHour(zone, hour.hour, round(celsius, 1), round(point, 1)))
    return sorted(risky, key=lambda r: (r.zone, r.hour))
