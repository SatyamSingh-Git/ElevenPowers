"""`--format markdown` works for the money reports too, with the CSV's values."""
import csv
from datetime import date
import io
import re

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
    fk("vehicle", "add", "VAN-112", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk("odometer", "add", "VAN-112", "3000", "--on", "2025-12-31")
    fk("fuel", "add", "VAN-112", "--gallons", "10", "--cost", "35.00", "--odometer", "3100",
       "--on", "2026-01-05")
    fk("fuel", "add", "VAN-112", "--gallons", "12", "--cost", "43.20", "--odometer", "3400",
       "--on", "2026-01-15")
    order = fk("wo", "open", "VAN-112", "--on", "2026-01-10").strip()
    fk("wo", "part", order, "--number", "BP-7", "--qty", "1", "--price", "30.00")
    fk("wo", "close", order, "--on", "2026-01-11")
    fk("odometer", "add", "VAN-112", "3500", "--on", "2026-01-31")
    return fk


def _cells(line):
    line = line.strip()
    line = line[1:] if line.startswith("|") else line
    line = line[:-1] if line.endswith("|") else line
    return [cell.strip() for cell in line.split("|")]


def _same_as_csv(fk, *command):
    lines = fk(*command, "--format", "markdown").strip().splitlines()
    expected = list(csv.reader(io.StringIO(fk(*command, "--format", "csv"))))
    assert _cells(lines[0]) == expected[0]
    assert all(re.fullmatch(r":?-{3,}:?", cell) for cell in _cells(lines[1]))
    assert [_cells(line) for line in lines[2:]] == expected[1:]
    return expected


def test_costs(fk):
    expected = _same_as_csv(fk, "costs", "--from", "2026-01-01", "--to", "2026-01-31")
    assert len(expected) == 2


def test_fuel_report(fk):
    expected = _same_as_csv(fk, "fuel", "report", "--from", "2026-01-01", "--to", "2026-01-31")
    assert len(expected) == 2


def test_spend(fk):
    _same_as_csv(fk, "spend", "--from", "2025-12-01", "--to", "2026-01-31")
