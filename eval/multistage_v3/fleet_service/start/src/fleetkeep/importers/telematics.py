"""Odometer readings from the vehicles' telematics units.

Columns: vehicle, timestamp (ISO 8601), odometer. Units report many times a
day; only each day's last report becomes a reading, and a day the fleet already
has a reading for, or a later one, is skipped.
"""
from datetime import datetime

from ..errors import FleetError
from ..model.readings import OdometerReading, parse_odometer
from ..model.vehicle import normalise_vehicle_id
from .source import ImportResult, read_rows

COLUMNS = ("vehicle", "timestamp", "odometer")


def _timestamp(text):
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        raise FleetError("E142", text=text) from None


def import_telematics(fleet, path):
    result, last_report = ImportResult(), {}
    for line, row in read_rows(path, COLUMNS):
        try:
            vehicle_id = fleet.vehicle(normalise_vehicle_id(row["vehicle"])).id
            stamp = _timestamp(row["timestamp"])
            odometer = parse_odometer(row["odometer"])
        except FleetError as error:
            result.rejected.append((line, str(error)))
            continue
        key = (vehicle_id, stamp.date())
        kept = last_report.get(key)
        if kept is not None and kept[0] > stamp:
            result.skipped.append((line, "a later report that day"))
            continue
        if kept is not None:
            result.skipped.append((kept[1], "a later report that day"))
        last_report[key] = (stamp, line, odometer)
    for (vehicle_id, day), (_, line, odometer) in sorted(last_report.items()):
        held = fleet.readings(vehicle_id)
        if held and held[-1].day >= day:
            result.skipped.append((line, "the fleet has a reading for that day or later"))
            continue
        try:
            fleet.add_reading(OdometerReading(vehicle_id, day, odometer))
        except FleetError as error:
            result.rejected.append((line, str(error)))
            continue
        result.imported += 1
    result.skipped.sort()
    result.rejected.sort()
    return result
