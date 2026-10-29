"""The fleet's logs, kept as CSV: readings, fill-ups, service history, fuel cards and tread."""
import csv
from datetime import date
from decimal import Decimal

from ..model.inspection import TreadReading
from ..model.readings import FuelEntry, OdometerReading
from ..model.workorder import ServiceRecord

READING_FIELDS = ("vehicle", "date", "odometer")
FUEL_FIELDS = ("vehicle", "date", "gallons", "cost", "odometer")
HISTORY_FIELDS = ("vehicle", "code", "date", "odometer", "order")
CARD_FIELDS = ("card", "vehicle")
TREAD_FIELDS = ("vehicle", "date", "position", "depth")


def _write(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(fields)
        writer.writerows(rows)


def _read(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_readings(path, readings):
    _write(path, READING_FIELDS,
           ((r.vehicle_id, r.day.isoformat(), r.odometer) for r in readings))


def read_readings(path):
    return [OdometerReading(row["vehicle"], date.fromisoformat(row["date"]), int(row["odometer"]))
            for row in _read(path)]


def write_fuel(path, entries):
    _write(path, FUEL_FIELDS, (
        (e.vehicle_id, e.day.isoformat(), e.gallons, e.cost, "" if e.odometer is None else e.odometer)
        for e in entries))


def read_fuel(path):
    return [FuelEntry(row["vehicle"], date.fromisoformat(row["date"]), Decimal(row["gallons"]),
                      int(row["cost"]), int(row["odometer"]) if row["odometer"] else None)
            for row in _read(path)]


def write_history(path, records):
    _write(path, HISTORY_FIELDS,
           ((r.vehicle_id, r.code, r.day.isoformat(), r.odometer, r.order_id) for r in records))


def read_history(path):
    return [ServiceRecord(row["vehicle"], row["code"], date.fromisoformat(row["date"]),
                          int(row["odometer"]), row["order"])
            for row in _read(path)]


def write_cards(path, cards):
    _write(path, CARD_FIELDS, cards)


def read_cards(path):
    return [(row["card"], row["vehicle"]) for row in _read(path)]


def write_treads(path, readings):
    _write(path, TREAD_FIELDS,
           ((r.vehicle_id, r.day.isoformat(), r.position, r.depth) for r in readings))


def read_treads(path):
    return [TreadReading(row["vehicle"], date.fromisoformat(row["date"]), row["position"],
                         int(row["depth"]))
            for row in _read(path)]
