"""Imports and the money reports, end to end through the command line."""
from datetime import date
from decimal import Decimal
import json

import pytest

from fleetkeep.cli.main import main
from fleetkeep.clock import FixedClock


@pytest.fixture
def fk(tmp_path, capsys):
    root = tmp_path / "fleet"

    def fk(*args):
        code = main(["--fleet", str(root), *map(str, args)], clock=FixedClock(date(2026, 3, 1)))
        out, err = capsys.readouterr()
        assert code == 0, err
        return out

    def write(name, text):
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path

    fk("init", "--name", "North")
    fk("vehicle", "add", "VAN-301", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-09-01", "--odometer", "2000")
    fk("vehicle", "add", "TRK-401", "--class", "heavy", "--make", "Volvo", "--model", "VNL",
       "--year", "2025", "--in-service", "2025-06-01", "--odometer", "40000")
    fk.write = write
    return fk


def _fuel_card(fk):
    fk("fuel", "card", "7001", "VAN-301")
    path = fk.write("card.csv", "Card,Unit,Date,Gallons,Amount,Odometer\n"
                                "5550,VAN-301,01/05/2026,18,$63.00,10000\n"
                                "7001,,01/19/2026,20,$72.00,10400\n"
                                "5550,van-301,01/28/2026,12,$45.60,10700\n"
                                "5550,VAN-301,01/05/2026,18,$63.00,10000\n"
                                "6100,TRK-401,01/10/2026,400,\"$1,480.00\",\n"
                                "6100,VAN-999,01/11/2026,20,$70.00,\n")
    return fk("fuel", "import", path).splitlines()


def _closed_order(fk):
    fk("odometer", "add", "VAN-301", "9900", "--on", "2025-12-31")
    order = fk("wo", "open", "VAN-301", "--service", "TIRE-ROT", "--on", "2026-01-20").strip()
    fk("wo", "part", order, "--number", "BP-7", "--description", "brake pads", "--qty", "2",
       "--price", "30.00")
    fk("wo", "labour", order, "--mechanic", "Ana", "--hours", "2")
    fk("wo", "close", order, "--on", "2026-01-21")
    fk("odometer", "add", "VAN-301", "10750", "--on", "2026-01-31")
    return order


def test_fuel_card_import(fk):
    lines = _fuel_card(fk)
    assert lines[0] == "imported 3, skipped 1, rejected 2"
    assert any(line.startswith("line 5: skipped:") for line in lines)
    assert any(line.startswith("line 6: rejected:") for line in lines)
    assert any(line.startswith("line 7: rejected:") and "E103" in line for line in lines)


def test_fuel_report(fk):
    _fuel_card(fk)
    rows = json.loads(fk("fuel", "report", "--from", "2026-01-01", "--to", "2026-01-31",
                         "--format", "json"))
    assert len(rows) == 1
    row = rows[0]
    assert (row["vehicle"], row["fills"], row["gallons"], row["fuel_cost"]) == (
        "VAN-301", 3, "50.000", "180.60")
    assert (row["miles"], row["mpg"]) == (700, "21.9")


def test_history_import_skips_codes_the_catalog_lacks(fk):
    path = fk.write("old.csv", "vehicle,code,date,odometer\n"
                               "VAN-301,OIL,2025-11-01,6000\n"
                               "VAN-301,WASH,2025-12-01,8000\n"
                               "TRK-401,AIR-BRAKE,2025-12-15,52000\n"
                               "VAN-777,OIL,2025-12-15,100\n")
    lines = fk("history", "import", path).splitlines()
    assert lines[0] == "imported 2, skipped 1, rejected 1"
    assert any(line.startswith("line 3: skipped:") and "WASH" in line for line in lines)
    assert any(line.startswith("line 5: rejected:") for line in lines)
    history = fk("history", "show", "VAN-301", "--format", "csv").splitlines()
    assert history[1:] == ["2025-11-01,OIL,Engine oil and filter,6000,"]


def test_timesheet_labour_matches_labour_entered_by_hand(fk):
    by_hand = fk("wo", "open", "TRK-401", "--service", "AIR-BRAKE", "--on", "2026-02-02").strip()
    fk("wo", "labour", by_hand, "--mechanic", "Ana", "--hours", "3")
    from_sheet = fk("wo", "open", "TRK-401", "--service", "OIL", "--on", "2026-02-03").strip()
    path = fk.write("week.csv", f"order,mechanic,hours,rate\n{from_sheet},Ben,3,\n")
    assert fk("timesheet", "import", path).splitlines()[0] == "imported 1, skipped 0, rejected 0"
    hand = json.loads(fk("wo", "show", by_hand, "--json"))
    sheet = json.loads(fk("wo", "show", from_sheet, "--json"))
    assert Decimal(hand["labour"]) > 0
    assert sheet["labour"] == hand["labour"]


def test_costs_carry_the_work_order_totals(fk):
    _fuel_card(fk)
    order = _closed_order(fk)
    total = Decimal(json.loads(fk("wo", "show", order, "--json"))["total"])
    assert total >= Decimal("250.00")
    rows = {row["vehicle"]: row for row in json.loads(
        fk("costs", "--from", "2026-01-01", "--to", "2026-01-31", "--format", "json"))}
    van = rows["VAN-301"]
    assert (van["miles"], Decimal(van["fuel"])) == (850, Decimal("180.60"))
    assert Decimal(van["maintenance"]) == total
    assert Decimal(van["total"]) == total + Decimal("180.60")
    assert Decimal(van["cost_per_mile"]) == ((total + Decimal("180.60")) / 850).quantize(Decimal("0.001"))
    assert Decimal(rows["TRK-401"]["maintenance"]) == 0


def test_spend_carries_the_work_order_totals(fk):
    _fuel_card(fk)
    order = _closed_order(fk)
    total = Decimal(json.loads(fk("wo", "show", order, "--json"))["total"])
    rows = {row["month"]: row for row in json.loads(
        fk("spend", "--from", "2026-01-01", "--to", "2026-02-28", "--format", "json"))}
    assert (rows["2026-01"]["orders"], Decimal(rows["2026-01"]["maintenance"])) == (1, total)
    assert Decimal(rows["2026-01"]["total"]) == total + Decimal("180.60")
    assert Decimal(rows["2026-02"]["total"]) == 0


def test_summary_agrees_with_the_reports(fk):
    _fuel_card(fk)
    _closed_order(fk)
    period = ("--from", "2026-01-01", "--to", "2026-01-31", "--format", "json")
    van = {row["vehicle"]: row for row in json.loads(fk("summary", *period))}["VAN-301"]
    costs = {row["vehicle"]: row for row in json.loads(fk("costs", *period))}["VAN-301"]
    assert (van["miles"], van["mpg"], van["days_down"]) == (850, "21.9", 1)
    assert (van["total"], van["cost_per_mile"]) == (costs["total"], costs["cost_per_mile"])
