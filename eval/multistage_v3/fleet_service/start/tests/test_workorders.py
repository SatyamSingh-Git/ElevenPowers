from datetime import date
from decimal import Decimal

import pytest

from fleetkeep.errors import FleetError
from fleetkeep.model.inspection import Defect
from fleetkeep.services import workorders
from fleetkeep.services.downtime import availability, days_down
from fleetkeep.model.dates import Period


def test_parts_from_stock_and_bought_in(fleet):
    order = workorders.open_order(fleet, "VAN-101", date(2026, 1, 5), ["OIL"])
    workorders.receive_parts(fleet, "OF-12", 4, 840, "oil filter")
    stocked = workorders.add_part(fleet, order.id, "OF-12", 1)
    bought = workorders.add_part(fleet, order.id, "WB-1", 2, 1299, "wiper blade")
    assert (stocked.unit_price, stocked.description) == (840, "oil filter")
    assert bought.amount == 2598
    assert fleet.stock_item("OF-12").on_hand == 3
    with pytest.raises(FleetError) as caught:
        workorders.add_part(fleet, order.id, "XX-9", 1)
    assert caught.value.code == "E132"


def test_labour_uses_the_fleet_rate_unless_given(fleet):
    order = workorders.open_order(fleet, "VAN-101", date(2026, 1, 5), ["OIL"])
    assert workorders.log_labour(fleet, order.id, "Ana", Decimal("1.5")).rate == 9500
    assert workorders.log_labour(fleet, order.id, "Ben", Decimal("1"), 12000).rate == 12000


def test_charges_add_parts_and_labour(fleet):
    order = workorders.open_order(fleet, "VAN-101", date(2026, 1, 5), ["OIL"])
    workorders.add_part(fleet, order.id, "OF-12", 2, 1250)
    workorders.log_labour(fleet, order.id, "Ana", Decimal("2"))
    charges = workorders.order_charges(order)
    assert (charges.parts, charges.labour, charges.total) == (2500, 19000, 21500)


def test_closing_records_services_and_fixes_defects(fleet):
    fleet.add_defect(Defect("D-0001", "VAN-101", date(2026, 1, 4), "brake light out"))
    order = workorders.open_order(fleet, "VAN-101", date(2026, 1, 5), ["OIL", "TIRE-ROT"],
                                  defects=["D-0001"])
    workorders.close_order(fleet, order.id, date(2026, 1, 6), odometer=5200)
    assert [(r.code, r.odometer, r.order_id) for r in fleet.history("VAN-101")] == [
        ("OIL", 5200, order.id), ("TIRE-ROT", 5200, order.id)]
    assert fleet.defect("D-0001").fixed == date(2026, 1, 6)
    with pytest.raises(FleetError) as caught:
        workorders.add_part(fleet, order.id, "OF-12", 1, 100)
    assert caught.value.code == "E122"


def test_cannot_close_before_opening(fleet):
    order = workorders.open_order(fleet, "VAN-101", date(2026, 1, 5), [])
    with pytest.raises(FleetError) as caught:
        workorders.close_order(fleet, order.id, date(2026, 1, 4))
    assert caught.value.code == "E123"


def test_cancelling(fleet):
    first = workorders.open_order(fleet, "VAN-101", date(2026, 1, 5), [])
    second = workorders.open_order(fleet, "VAN-101", date(2026, 1, 5), [])
    workorders.cancel_order(fleet, first.id)
    assert workorders.open_order(fleet, "VAN-101", date(2026, 1, 6), []).id == "WO-0003"
    workorders.add_part(fleet, second.id, "OF-12", 1, 100)
    with pytest.raises(FleetError) as caught:
        workorders.cancel_order(fleet, second.id)
    assert caught.value.code == "E125"


def test_downtime_counts_nights_in_the_shop(fleet):
    planned = workorders.open_order(fleet, "VAN-101", date(2026, 1, 10), [])
    workorders.close_order(fleet, planned.id, date(2026, 1, 13))
    same_day = workorders.open_order(fleet, "VAN-101", date(2026, 1, 20), [])
    workorders.close_order(fleet, same_day.id, date(2026, 1, 20))
    workorders.open_order(fleet, "VAN-101", date(2026, 1, 30), [], breakdown=True)
    january = Period(date(2026, 1, 1), date(2026, 1, 31))
    assert days_down(fleet, "VAN-101", january) == 5
    assert days_down(fleet, "VAN-101", january, breakdowns_only=True) == 2
    assert availability(fleet, "VAN-101", january) == Decimal("83.9")
