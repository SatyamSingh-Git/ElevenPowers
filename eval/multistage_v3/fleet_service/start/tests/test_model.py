from datetime import date
from decimal import Decimal

import pytest

from fleetkeep.errors import FleetError
from fleetkeep.model.dates import Period, add_months, parse_date
from fleetkeep.model.money import divide, format_money, parse_money, times
from fleetkeep.model.readings import FuelEntry, parse_gallons
from fleetkeep.model.stock import StockItem
from fleetkeep.model.vehicle import Vehicle, normalise_vehicle_id
from fleetkeep.model.workorder import LabourLine, parse_hours


@pytest.mark.parametrize("text, cents", [("12.5", 1250), ("$1,204.50", 120450), ("0", 0)])
def test_parse_money(text, cents):
    assert parse_money(text) == cents


@pytest.mark.parametrize("text", ["abc", "-1", "1.005", "nan"])
def test_parse_money_rejects(text):
    with pytest.raises(FleetError) as caught:
        parse_money(text)
    assert caught.value.code == "E141"


def test_money_arithmetic_rounds_half_up():
    assert times(9500, Decimal("1.25")) == 11875
    assert times(333, Decimal("0.5")) == 167
    assert divide(1000, 3) == 333
    assert format_money(120450) == "1204.50"


def test_add_months_keeps_the_day_or_takes_the_last():
    assert add_months(date(2026, 1, 15), 6) == date(2026, 7, 15)
    assert add_months(date(2026, 8, 31), 6) == date(2027, 2, 28)
    assert add_months(date(2025, 11, 30), 3) == date(2026, 2, 28)


def test_period_is_inclusive():
    period = Period(date(2026, 1, 1), date(2026, 1, 31))
    assert period.days == 31
    assert date(2026, 1, 31) in period
    assert date(2026, 2, 1) not in period
    with pytest.raises(FleetError):
        Period(date(2026, 2, 1), date(2026, 1, 1))


def test_parse_date_error():
    with pytest.raises(FleetError) as caught:
        parse_date("01/02/2026")
    assert str(caught.value) == "E142 invalid date: 01/02/2026"


def test_vehicle_ids_are_upper_cased_and_checked():
    assert normalise_vehicle_id(" van-101 ") == "VAN-101"
    with pytest.raises(FleetError) as caught:
        normalise_vehicle_id("VAN101")
    assert caught.value.code == "E101"


def test_vehicle_rules():
    with pytest.raises(FleetError) as caught:
        Vehicle("VAN-101", "bus", "Ford", "Transit", 2025, date(2025, 9, 1))
    assert caught.value.code == "E102"
    with pytest.raises(FleetError) as caught:
        Vehicle("VAN-101", "light", "Ford", "Transit", 1975, date(2025, 9, 1))
    assert str(caught.value) == "E108 model year 1975 is outside 1980-2026"


def test_fill_up_limits():
    with pytest.raises(FleetError) as caught:
        FuelEntry("VAN-101", date(2026, 1, 1), Decimal("0"), 100)
    assert caught.value.code == "E111"
    with pytest.raises(FleetError) as caught:
        FuelEntry("VAN-101", date(2026, 1, 1), Decimal("151"), 100)
    assert caught.value.code == "E112"
    assert parse_gallons("12.3456") == Decimal("12.346")


def test_labour_amount_and_hours():
    assert LabourLine("Ana", Decimal("1.5"), 9500).amount == 14250
    assert parse_hours("2") == Decimal("2.00")
    for bad in ("0", "25", "x"):
        with pytest.raises(FleetError):
            parse_hours(bad)


def test_stock_is_valued_at_average_cost():
    item = StockItem("OF-12", "oil filter")
    item.receive(10, 840)
    item.receive(10, 900)
    assert (item.on_hand, item.unit_cost) == (20, 870)
    item.issue(5)
    assert (item.on_hand, item.unit_cost, item.value) == (15, 870, 13050)
    with pytest.raises(FleetError) as caught:
        item.issue(16)
    assert str(caught.value) == "E131 not enough OF-12 in stock: 15 on hand"
