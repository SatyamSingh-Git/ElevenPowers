"""Loading readings back from the readings log."""
import csv
from pathlib import Path

from ..core.clock import parse_timestamp
from ..core.model import Reading


def load_readings(path, *, day=None, zone=None):
    """Readings from the log, in log order, optionally only one day or zone."""
    path = Path(path)
    if not path.exists():
        return []
    readings = []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.reader(handle)
        next(rows, None)
        for row in rows:
            if not row:
                continue
            stamp, zone_id, sensor, kind, value, unit = row
            at = parse_timestamp(stamp)
            if day is not None and at.date() != day:
                continue
            if zone is not None and zone_id != zone:
                continue
            readings.append(
                Reading(at=at, zone=zone_id, sensor=sensor, kind=kind, value=float(value), unit=unit)
            )
    return readings


def latest_by_sensor(readings):
    """Each sensor's most recent reading; a later row wins a tie."""
    latest = {}
    for reading in readings:
        current = latest.get(reading.sensor)
        if current is None or reading.at >= current.at:
            latest[reading.sensor] = reading
    return latest
