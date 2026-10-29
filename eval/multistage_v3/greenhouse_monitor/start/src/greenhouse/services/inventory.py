"""Sensor inventory: every sensor seen in the readings, where and how often it reports."""
from dataclasses import dataclass
from datetime import datetime
from statistics import median


@dataclass(frozen=True)
class SensorInfo:
    sensor: str
    zone: str
    kind: str
    first_seen: datetime
    last_seen: datetime
    count: int
    interval_minutes: float | None


def inventory(readings):
    """One SensorInfo per sensor, sorted by sensor id.

    The zone and kind are the ones the sensor last reported with; the
    interval is the median time between its readings.
    """
    seen = {}
    for reading in readings:
        seen.setdefault(reading.sensor, []).append(reading)
    return [_info(sensor, sorted(items, key=lambda r: r.at)) for sensor, items in sorted(seen.items())]


def _info(sensor, items):
    steps = [(later.at - earlier.at).total_seconds() / 60 for earlier, later in zip(items, items[1:])]
    last = items[-1]
    return SensorInfo(
        sensor=sensor,
        zone=last.zone,
        kind=last.kind,
        first_seen=items[0].at,
        last_seen=last.at,
        count=len(items),
        interval_minutes=median(steps) if steps else None,
    )


def moved(readings):
    """Sensors that reported from more than one zone, with the zones in order of first report."""
    zones = {}
    for reading in readings:
        found = zones.setdefault(reading.sensor, [])
        if reading.zone not in found:
            found.append(reading.zone)
    return {sensor: found for sensor, found in sorted(zones.items()) if len(found) > 1}
