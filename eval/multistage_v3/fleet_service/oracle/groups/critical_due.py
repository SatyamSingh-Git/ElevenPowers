"""Services far past a limit are `critical` and lead the due list."""
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
    for vehicle in ("VAN-501", "VAN-502"):
        fk("vehicle", "add", vehicle, "--class", "light", "--make", "Ford", "--model", "Transit",
           "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk.root = root
    return fk


def _due(fk, as_of):
    rows = json.loads(fk("due", "--as-of", as_of, "--format", "json"))
    return rows, {(row["vehicle"], row["code"]): row["status"] for row in rows}


def test_more_than_the_mileage_margin_is_critical(fk):
    # OIL every 7500 miles, tyre rotation every 6000.
    fk("odometer", "add", "VAN-501", "8501", "--on", "2026-02-20")
    fk("odometer", "add", "VAN-502", "7000", "--on", "2026-02-20")
    _, status = _due(fk, "2026-02-21")
    assert status["VAN-501", "OIL"] == "critical"
    assert status["VAN-501", "TIRE-ROT"] == "critical"
    assert status["VAN-502", "TIRE-ROT"] == "overdue"
    assert status["VAN-502", "OIL"] == "due-soon"


def test_exactly_the_margin_is_still_overdue(fk):
    fk("odometer", "add", "VAN-501", "8500", "--on", "2026-02-20")
    _, status = _due(fk, "2026-02-21")
    assert status["VAN-501", "OIL"] == "overdue"


def test_more_than_the_days_margin_is_critical(fk):
    # OIL is due six months after entering service: 2026-04-01.
    _, status = _due(fk, "2026-05-01")
    assert status["VAN-501", "OIL"] == "overdue"
    _, status = _due(fk, "2026-05-02")
    assert status["VAN-501", "OIL"] == "critical"


def test_critical_services_come_before_overdue_ones(fk):
    fk("odometer", "add", "VAN-501", "6500", "--on", "2026-02-20")
    fk("odometer", "add", "VAN-502", "8600", "--on", "2026-02-20")
    rows, _ = _due(fk, "2026-02-21")
    statuses = [row["status"] for row in rows]
    assert statuses[:2] == ["critical", "critical"]
    assert {(row["vehicle"], row["code"]) for row in rows[:2]} == {
        ("VAN-502", "OIL"), ("VAN-502", "TIRE-ROT")}
    assert statuses[2] == "overdue"
    assert (rows[2]["vehicle"], rows[2]["code"]) == ("VAN-501", "TIRE-ROT")
