"""Readings over a range of days as CSV or JSON, for the agronomists' spreadsheets."""
import csv
import io
import json

from ..core.clock import format_timestamp
from ..core.errors import ValidationError
from .formatting import number

EXPORT_FIELDS = ("timestamp", "zone", "sensor", "kind", "value", "unit")


def export_record(reading):
    return {
        "timestamp": format_timestamp(reading.at),
        "zone": reading.zone,
        "sensor": reading.sensor,
        "kind": reading.kind,
        "value": reading.value,
        "unit": reading.unit,
    }


def export_csv(readings):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_FIELDS, lineterminator="\n")
    writer.writeheader()
    for reading in readings:
        writer.writerow({**export_record(reading), "value": number(reading.kind, reading.value)})
    return buffer.getvalue().rstrip("\n")


def export_json(readings):
    return json.dumps([export_record(reading) for reading in readings], indent=2)


EXPORTERS = {"csv": export_csv, "json": export_json}


def export_readings(fmt, readings):
    try:
        exporter = EXPORTERS[fmt]
    except KeyError:
        raise ValidationError(f"unknown format: {fmt}") from None
    return exporter(readings)
