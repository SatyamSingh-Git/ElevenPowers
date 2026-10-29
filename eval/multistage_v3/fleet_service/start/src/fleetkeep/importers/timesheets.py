"""Labour from the mechanics' weekly timesheets.

Columns: order, mechanic, hours, rate. `rate` is left blank for ordinary work,
which is charged at the shop's labour rate, and filled in for jobs quoted at a
different rate. A timesheet goes in whole or not at all: if any row is bad,
nothing is charged and every bad row is listed.
"""
from ..errors import FleetError
from ..model.money import parse_money
from ..model.workorder import LabourLine, parse_hours
from .source import ImportResult, read_rows

COLUMNS = ("order", "mechanic", "hours", "rate")


def _line(fleet, row):
    rate = parse_money(row["rate"]) if row["rate"] else fleet.settings.labour_rate
    return LabourLine(row["mechanic"], parse_hours(row["hours"]), rate)


def import_timesheet(fleet, path):
    result, charges = ImportResult(), []
    for line, row in read_rows(path, COLUMNS):
        try:
            order = fleet.order(row["order"].upper())
            if not order.is_open:
                raise FleetError("E122", order=order.id)
            charges.append((order, _line(fleet, row)))
        except FleetError as error:
            result.rejected.append((line, str(error)))
    if result.rejected:
        return result
    for order, labour in charges:
        order.add_line(labour)
    result.imported = len(charges)
    return result
