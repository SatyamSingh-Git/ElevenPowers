"""The fuel report's columns, in order, in every format."""
from datetime import date
import json

import pytest

from fleetkeep.cli.main import main
from fleetkeep.clock import FixedClock

COLUMNS = ["vehicle", "fills", "gallons", "fuel_cost", "cost_per_gallon", "miles", "mpg"]


@pytest.fixture
def fk(tmp_path, capsys):
    root = tmp_path / "fleet"

    def fk(*args):
        code = main(["--fleet", str(root), *map(str, args)], clock=FixedClock(date(2026, 3, 1)))
        out, err = capsys.readouterr()
        assert code == 0, err
        return out

    fk("init", "--name", "North")
    fk("vehicle", "add", "VAN-903", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk("fuel", "add", "VAN-903", "--gallons", "10", "--cost", "35.00", "--odometer", "5000",
       "--on", "2026-01-05")
    fk("fuel", "add", "VAN-903", "--gallons", "10", "--cost", "36.00", "--odometer", "5250",
       "--on", "2026-01-12")
    return fk


def _report(fk, fmt):
    return fk("fuel", "report", "--from", "2026-01-01", "--to", "2026-01-31", "--format", fmt)


def test_csv(fk):
    lines = _report(fk, "csv").splitlines()
    assert lines[0] == ",".join(COLUMNS)
    assert lines[1] == "VAN-903,2,20.000,71.00,3.55,250,25.0"


def test_json(fk):
    rows = json.loads(_report(fk, "json"))
    assert list(rows[0]) == COLUMNS


def test_table(fk):
    lines = _report(fk, "table").splitlines()
    assert lines[0].split() == COLUMNS
    assert lines[2].split() == ["VAN-903", "2", "20.000", "71.00", "3.55", "250", "25.0"]
