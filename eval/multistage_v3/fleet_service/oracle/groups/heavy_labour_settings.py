"""`heavy_labour_rate` in fleet.ini sets the heavy rate, independently of `labour_rate`."""
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
    fk("vehicle", "add", "TRK-302", "--class", "heavy", "--make", "Volvo", "--model", "VNL",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk("vehicle", "add", "VAN-302", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk.ini = root / "fleet.ini"
    return fk


def _labour(fk, vehicle):
    order = fk("wo", "open", vehicle, "--on", "2026-02-02").strip()
    fk("wo", "labour", order, "--mechanic", "Ana", "--hours", "2")
    return Decimal(str(json.loads(fk("wo", "show", order, "--json"))["labour"]))


def test_heavy_rate_from_fleet_ini(fk):
    fk.ini.write_text("[fleet]\nname = North\nheavy_labour_rate = 140.00\n", encoding="utf-8")
    assert _labour(fk, "TRK-302") == Decimal("280.00")
    assert _labour(fk, "VAN-302") == Decimal("190.00")


def test_labour_rate_leaves_heavy_alone(fk):
    fk.ini.write_text("[fleet]\nname = North\nlabour_rate = 80.00\n", encoding="utf-8")
    assert _labour(fk, "TRK-302") == Decimal("250.00")
    assert _labour(fk, "VAN-302") == Decimal("160.00")
