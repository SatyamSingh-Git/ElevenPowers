"""Vehicles from the leasing company's delivery schedule.

Columns: id, class, make, model, year, in_service (YYYY-MM-DD), odometer.
A vehicle the fleet already has is skipped, so the whole schedule can be
imported again each time new deliveries are added to it.
"""
from ..errors import FleetError
from ..model.dates import parse_date
from ..model.readings import parse_odometer
from ..model.vehicle import Vehicle, normalise_vehicle_id
from .source import ImportResult, read_rows

COLUMNS = ("id", "class", "make", "model", "year", "in_service", "odometer")


def _year(text):
    try:
        return int(text)
    except ValueError:
        raise FleetError("E143", text=text) from None


def import_vehicles(fleet, path):
    result = ImportResult()
    known = {vehicle.id for vehicle in fleet.vehicles()}
    for line, row in read_rows(path, COLUMNS):
        try:
            vehicle = Vehicle(normalise_vehicle_id(row["id"]), row["class"].lower(), row["make"],
                              row["model"], _year(row["year"]), parse_date(row["in_service"]),
                              parse_odometer(row["odometer"] or "0"))
        except FleetError as error:
            result.rejected.append((line, str(error)))
            continue
        if vehicle.id in known:
            result.skipped.append((line, f"already in the fleet: {vehicle.id}"))
            continue
        fleet.add_vehicle(vehicle)
        known.add(vehicle.id)
        result.imported += 1
    return result
