"""Work orders, the due list and reminders, end to end through the command line."""
from datetime import date
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

    fk("init", "--name", "North")
    fk("vehicle", "add", "VAN-101", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "1000")
    fk("vehicle", "add", "VAN-102", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "500")
    fk("vehicle", "add", "TRK-201", "--class", "heavy", "--make", "Volvo", "--model", "VNL",
       "--year", "2025", "--in-service", "2025-11-01", "--odometer", "20000")
    fk("odometer", "add", "VAN-101", "10600", "--on", "2026-02-25")
    fk("odometer", "add", "VAN-102", "4100", "--on", "2025-12-01")
    first = fk("wo", "open", "VAN-102", "--service", "OIL", "--on", "2025-12-01").strip()
    fk("wo", "part", first, "--number", "OF-12", "--description", "oil filter", "--qty", "1",
       "--price", "12.40")
    fk("wo", "close", first, "--on", "2025-12-02")
    fk("odometer", "add", "VAN-102", "5000", "--on", "2026-01-10")
    second = fk("wo", "open", "VAN-102", "--service", "TIRE-ROT", "--on", "2026-01-10").strip()
    fk("wo", "part", second, "--number", "VS-4", "--description", "valve stem", "--qty", "4",
       "--price", "4.25")
    fk("wo", "labour", second, "--mechanic", "Ana", "--hours", "1.5")
    fk("wo", "close", second, "--on", "2026-01-12")
    fk("odometer", "add", "VAN-102", "11200", "--on", "2026-02-20")
    fk("odometer", "add", "TRK-201", "27800", "--on", "2026-02-26")
    fk.orders = (first, second)
    return fk


def _due(fk):
    rows = json.loads(fk("due", "--as-of", "2026-03-01", "--format", "json"))
    return rows, {(row["vehicle"], row["code"]): row for row in rows}


def test_due_figures(fk):
    rows, due = _due(fk)
    assert len(rows) == 8 + 8 + 9
    assert (due["VAN-102", "TIRE-ROT"]["due_miles"], due["VAN-102", "TIRE-ROT"]["remaining_miles"],
            due["VAN-102", "TIRE-ROT"]["status"]) == (11000, -200, "overdue")
    assert (due["VAN-102", "OIL"]["due_miles"], due["VAN-102", "OIL"]["remaining_miles"],
            due["VAN-102", "OIL"]["due_date"], due["VAN-102", "OIL"]["status"]) == (
        11600, 400, "2026-06-02", "due-soon")
    assert (due["TRK-201", "OIL"]["remaining_miles"], due["TRK-201", "OIL"]["status"]) == (-300, "overdue")
    assert (due["TRK-201", "AIR-BRAKE"]["due_date"], due["TRK-201", "AIR-BRAKE"]["remaining_days"],
            due["TRK-201", "AIR-BRAKE"]["status"]) == ("2026-02-01", -28, "overdue")
    assert (due["VAN-101", "OIL"]["due_miles"], due["VAN-101", "OIL"]["remaining_miles"]) == (8500, -2100)
    assert (due["VAN-101", "TIRE-ROT"]["remaining_miles"]) == -3600
    assert due["VAN-101", "AIR-FILTER"]["status"] == "ok"


def test_due_order_puts_problems_first(fk):
    rows, _ = _due(fk)
    statuses = [row["status"] for row in rows]
    first_ok = statuses.index("ok")
    assert "ok" not in statuses[:first_ok] and set(statuses[first_ok:]) == {"ok"}
    soon = [i for i, status in enumerate(statuses) if status == "due-soon"]
    overdue = [i for i, status in enumerate(statuses) if status == "overdue"]
    assert max(overdue) < min(soon)
    assert {(row["vehicle"], row["code"]) for row in rows[:first_ok]} == {
        ("VAN-101", "OIL"), ("VAN-101", "TIRE-ROT"), ("VAN-102", "TIRE-ROT"), ("VAN-102", "OIL"),
        ("TRK-201", "OIL"), ("TRK-201", "AIR-BRAKE")}


def test_reminders_cover_every_service_that_needs_booking(fk):
    lines = fk("remind", "--as-of", "2026-03-01").splitlines()
    expected = {("VAN-101", "OIL", "Engine oil and filter"), ("VAN-101", "TIRE-ROT", "Tyre rotation"),
                ("VAN-102", "TIRE-ROT", "Tyre rotation"), ("VAN-102", "OIL", "Engine oil and filter"),
                ("TRK-201", "OIL", "Engine oil and filter"),
                ("TRK-201", "AIR-BRAKE", "Air brake adjustment")}
    assert len(lines) == len(expected)
    for vehicle, code, name in expected:
        assert any(vehicle in line and (code in line or name in line) for line in lines), (vehicle, code)


def test_work_orders_record_charges_and_history(fk):
    first, second = fk.orders
    shown = json.loads(fk("wo", "show", second, "--json"))
    assert (shown["status"], shown["opened"], shown["closed"]) == ("closed", "2026-01-10", "2026-01-12")
    assert (shown["parts"], shown["labour"]) == ("17.00", "142.50")
    assert json.loads(fk("wo", "show", first, "--json"))["parts"] == "12.40"
    history = fk("history", "show", "VAN-102", "--format", "csv").splitlines()
    assert history[1:] == [f"2025-12-02,OIL,Engine oil and filter,4100,{first}",
                           f"2026-01-12,TIRE-ROT,Tyre rotation,5000,{second}"]


def test_overdue_work_is_cleared_by_a_work_order(fk):
    order = fk("wo", "open", "TRK-201", "--service", "OIL", "--on", "2026-02-27").strip()
    fk("wo", "close", order, "--on", "2026-02-28", "--odometer", "27900")
    _, due = _due(fk)
    assert (due["TRK-201", "OIL"]["due_miles"], due["TRK-201", "OIL"]["status"]) == (35400, "ok")
    lines = fk("remind", "--as-of", "2026-03-01").splitlines()
    assert not any("TRK-201" in line and ("(OIL)" in line or "Engine oil" in line) for line in lines)
