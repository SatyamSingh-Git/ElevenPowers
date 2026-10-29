"""Fuel-card imports accept fill-ups up to 250 gallons."""
from datetime import date

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
    fk("vehicle", "add", "TNK-402", "--class", "heavy", "--make", "Kenworth", "--model", "T880",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk.root = tmp_path
    return fk


def test_large_fill_ups_import(fk):
    path = fk.root / "card.csv"
    path.write_text("Card,Unit,Date,Gallons,Amount,Odometer\n"
                    "8800,TNK-402,02/02/2026,240,$864.00,1000\n"
                    "8800,TNK-402,02/09/2026,175.5,$631.80,2200\n"
                    "8800,TNK-402,02/16/2026,260,$936.00,3400\n", encoding="utf-8")
    lines = fk("fuel", "import", path).splitlines()
    assert lines[0] == "imported 2, skipped 0, rejected 1"
    assert any(line.startswith("line 4: rejected:") and "E112" in line for line in lines)
