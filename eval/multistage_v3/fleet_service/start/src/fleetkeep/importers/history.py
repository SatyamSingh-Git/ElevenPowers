"""Service history carried over from the fleet's previous maintenance system.

Columns: vehicle, code, date (YYYY-MM-DD), odometer. The old system tracked
jobs this catalog does not schedule, such as washes and detailing; rows for
codes the catalog does not know are skipped and listed, not rejected, so a
migration can be run in one pass.
"""
from ..errors import FleetError
from ..model.dates import parse_date
from ..model.readings import parse_odometer
from ..model.vehicle import normalise_vehicle_id
from .source import ImportResult, read_rows

COLUMNS = ("vehicle", "code", "date", "odometer")


def import_history(fleet, path):
    result = ImportResult()
    for line, row in read_rows(path, COLUMNS):
        code = row["code"].upper()
        try:
            vehicle_id = normalise_vehicle_id(row["vehicle"])
            day = parse_date(row["date"])
            odometer = parse_odometer(row["odometer"])
            fleet.record_service(vehicle_id, code, day, odometer)
        except KeyError:
            result.skipped.append((line, f"not in the catalog: {code}"))
        except FleetError as error:
            result.rejected.append((line, str(error)))
        else:
            result.imported += 1
    return result
