"""`fleetkeep fuel add` accepts fill-ups up to 250 gallons."""
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
        return code, out, err

    fk("init", "--name", "North")
    fk("vehicle", "add", "TNK-401", "--class", "heavy", "--make", "Kenworth", "--model", "T880",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    return fk


def test_up_to_250_gallons(fk):
    assert fk("fuel", "add", "TNK-401", "--gallons", "180", "--cost", "650.00",
              "--on", "2026-02-02")[0] == 0
    assert fk("fuel", "add", "TNK-401", "--gallons", "250", "--cost", "900.00",
              "--on", "2026-02-03")[0] == 0
    assert len(fk("fuel", "list", "TNK-401")[1].splitlines()) == 2


def test_over_250_gallons_refused(fk):
    code, _, err = fk("fuel", "add", "TNK-401", "--gallons", "250.5", "--cost", "900.00",
                      "--on", "2026-02-03")
    assert code == 1
    assert "E112" in err
