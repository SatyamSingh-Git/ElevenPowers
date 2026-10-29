"""`fleetkeep fuel report` shows what each vehicle paid per gallon."""
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

    fk("init", "--name", "North")
    for vehicle in ("VAN-901", "VAN-902"):
        fk("vehicle", "add", vehicle, "--class", "light", "--make", "Ford", "--model", "Transit",
           "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk("fuel", "add", "VAN-901", "--gallons", "18", "--cost", "63.00", "--odometer", "10000",
       "--on", "2026-01-05")
    fk("fuel", "add", "VAN-901", "--gallons", "20", "--cost", "72.00", "--odometer", "10400",
       "--on", "2026-01-19")
    fk("fuel", "add", "VAN-901", "--gallons", "12", "--cost", "45.60", "--odometer", "10700",
       "--on", "2026-01-28")
    fk("fuel", "add", "VAN-902", "--gallons", "16", "--cost", "56.00", "--on", "2026-01-07")
    return fk


def _rows(fk):
    return {row["vehicle"]: row for row in json.loads(
        fk("fuel", "report", "--from", "2026-01-01", "--to", "2026-01-31", "--format", "json"))}


def test_cost_per_gallon(fk):
    rows = _rows(fk)
    assert Decimal(str(rows["VAN-901"]["cost_per_gallon"])) == Decimal("3.61")
    assert Decimal(str(rows["VAN-902"]["cost_per_gallon"])) == Decimal("3.50")


def test_other_columns_unchanged(fk):
    van = _rows(fk)["VAN-901"]
    assert (van["fills"], van["gallons"], van["fuel_cost"], van["miles"], van["mpg"]) == (
        3, "50.000", "180.60", 700, "21.9")
