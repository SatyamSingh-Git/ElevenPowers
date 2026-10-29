"""`shop_supplies_percent` and `shop_supplies_cap` in fleet.ini set the supplies charge."""
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
    fk("vehicle", "add", "VAN-702", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk.ini = root / "fleet.ini"
    return fk


def _shown(fk, hours):
    order = fk("wo", "open", "VAN-702", "--on", "2026-02-02").strip()
    fk("wo", "labour", order, "--mechanic", "Ana", "--hours", hours, "--rate", "100.00")
    shown = json.loads(fk("wo", "show", order, "--json"))
    return Decimal(str(shown["supplies"])), Decimal(str(shown["total"]))


def test_percentage_from_fleet_ini(fk):
    fk.ini.write_text("[fleet]\nname = North\nshop_supplies_percent = 10\n", encoding="utf-8")
    assert _shown(fk, "2") == (Decimal("20.00"), Decimal("220.00"))


def test_cap_from_fleet_ini(fk):
    fk.ini.write_text("[fleet]\nname = North\nshop_supplies_cap = 15.00\n", encoding="utf-8")
    assert _shown(fk, "4") == (Decimal("15.00"), Decimal("415.00"))


def test_zero_percent_charges_nothing(fk):
    fk.ini.write_text("[fleet]\nname = North\nshop_supplies_percent = 0\n", encoding="utf-8")
    assert _shown(fk, "4") == (Decimal("0"), Decimal("400.00"))


def test_defaults(fk):
    fk.ini.write_text("[fleet]\nname = North\n", encoding="utf-8")
    assert _shown(fk, "4") == (Decimal("20.00"), Decimal("420.00"))
    assert _shown(fk, "9") == (Decimal("40.00"), Decimal("940.00"))
