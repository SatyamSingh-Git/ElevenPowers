from datetime import date
from decimal import Decimal
import json

from fleetkeep.model.dates import Period
from fleetkeep.model.readings import FuelEntry, OdometerReading
from fleetkeep.reports.costs import cost_rows
from fleetkeep.reports.fuel import fuel_rows
from fleetkeep.reports.render import render
from fleetkeep.reports.spend import spend_rows
from fleetkeep.services import workorders

JANUARY = Period(date(2026, 1, 1), date(2026, 1, 31))


def test_costs_per_mile(fleet):
    fleet.add_reading(OdometerReading("VAN-101", date(2025, 12, 31), 4000))
    fleet.add_reading(OdometerReading("VAN-101", date(2026, 1, 31), 5600))
    fleet.add_fuel(FuelEntry("VAN-101", date(2026, 1, 10), Decimal("20"), 7000, 4500))
    order = workorders.open_order(fleet, "VAN-101", date(2026, 1, 12), [])
    workorders.add_part(fleet, order.id, "BR-2", 1, 18000)
    workorders.close_order(fleet, order.id, date(2026, 1, 12))
    rows = {row[0]: row for row in cost_rows(fleet, JANUARY)}
    assert rows["VAN-101"] == ("VAN-101", 1600, Decimal("70.00"), Decimal("180.00"),
                               Decimal("250.00"), Decimal("0.156"))
    assert rows["TRK-201"][1:] == (0, Decimal("0.00"), Decimal("0.00"), Decimal("0.00"), None)


def test_fuel_economy_uses_full_tanks(fleet):
    for day, gallons, cost, odometer in [(5, "20", 7000, 4000), (12, "15", 5250, 4300),
                                         (20, "10", 3500, None), (26, "25", 8750, 4800)]:
        fleet.add_fuel(FuelEntry("VAN-101", date(2026, 1, day), Decimal(gallons), cost, odometer))
    assert fuel_rows(fleet, JANUARY) == [
        ("VAN-101", 4, Decimal("70"), Decimal("245.00"), 800, Decimal("20.0"))]


def test_spend_by_month(fleet):
    fleet.add_fuel(FuelEntry("VAN-101", date(2026, 1, 10), Decimal("20"), 7000))
    order = workorders.open_order(fleet, "VAN-101", date(2026, 1, 30), [])
    workorders.add_part(fleet, order.id, "BR-2", 1, 18000)
    workorders.close_order(fleet, order.id, date(2026, 2, 2))
    rows = spend_rows(fleet, Period(date(2025, 12, 15), date(2026, 2, 28)))
    assert [row[0] for row in rows] == ["2025-12", "2026-01", "2026-02"]
    assert rows[1][1:] == (Decimal("70.00"), 0, Decimal("0.00"), Decimal("70.00"))
    assert rows[2][1:] == (Decimal("0.00"), 1, Decimal("180.00"), Decimal("180.00"))


def test_render_formats():
    rows = [("VAN-101", "OIL", "Engine oil and filter", 7600, -50, date(2026, 3, 1), 5, "overdue")]
    table = render("due", rows, "table").splitlines()
    assert table[0].split() == ["vehicle", "code", "service", "due_miles", "remaining_miles",
                                "due_date", "remaining_days", "status"]
    assert render("due", rows, "csv").splitlines()[1] == (
        "VAN-101,OIL,Engine oil and filter,7600,-50,2026-03-01,5,overdue")
    record = json.loads(render("due", rows, "json"))[0]
    assert (record["due_date"], record["remaining_miles"]) == ("2026-03-01", -50)
