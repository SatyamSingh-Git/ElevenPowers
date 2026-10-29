"""Fill-ups from the fuel-card provider's monthly transaction export.

The export has one row per card transaction. `Unit` is the vehicle id the
driver keyed in at the pump; when it is blank the card's assigned vehicle is
used. `Date` is MM/DD/YYYY, `Amount` is in dollars and may carry a `$` and
thousands separators, and `Odometer` is blank or 0 when the driver skipped it. Providers re-send overlapping months, so a transaction the
fleet already holds is skipped rather than counted twice.
"""
from datetime import datetime

from ..errors import FleetError
from ..model.money import parse_money
from ..model.readings import FuelEntry, parse_gallons, parse_odometer
from ..model.vehicle import normalise_vehicle_id
from .source import ImportResult, read_rows

COLUMNS = ("Card", "Unit", "Date", "Gallons", "Amount", "Odometer")
DATE_FORMAT = "%m/%d/%Y"


def _day(text):
    try:
        return datetime.strptime(text, DATE_FORMAT).date()
    except ValueError:
        raise FleetError("E142", text=text) from None


def _entry(fleet, row):
    odometer = parse_odometer(row["Odometer"]) if row["Odometer"] else 0
    unit = row["Unit"] or fleet.card_vehicle(row["Card"])
    return FuelEntry(
        vehicle_id=normalise_vehicle_id(unit),
        day=_day(row["Date"]),
        gallons=parse_gallons(row["Gallons"]),
        cost=parse_money(row["Amount"]),
        odometer=odometer or None,
    )


def import_fuel_card(fleet, path):
    result = ImportResult()
    for line, row in read_rows(path, COLUMNS):
        try:
            entry = _entry(fleet, row)
            held = fleet.fuel(fleet.vehicle(entry.vehicle_id).id)
        except FleetError as error:
            result.rejected.append((line, str(error)))
            continue
        if any(entry.same_purchase(other) for other in held):
            result.skipped.append((line, "already imported"))
            continue
        fleet.add_fuel(entry)
        result.imported += 1
    return result
