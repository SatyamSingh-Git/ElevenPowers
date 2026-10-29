"""Work orders carry a shop supplies charge on their labour, capped per order."""
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
    fk("vehicle", "add", "VAN-701", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    return fk


def _order(fk, hours=None, price="30.00"):
    order = fk("wo", "open", "VAN-701", "--service", "OIL", "--on", "2026-02-02").strip()
    fk("wo", "part", order, "--number", "BP-7", "--qty", "1", "--price", price)
    if hours:
        fk("wo", "labour", order, "--mechanic", "Ana", "--hours", hours, "--rate", "95.00")
    return order


def _money(shown, key):
    return Decimal(str(shown[key]))


def test_five_percent_of_the_labour(fk):
    shown = json.loads(fk("wo", "show", _order(fk, "2"), "--json"))
    assert _money(shown, "labour") == Decimal("190.00")
    assert _money(shown, "supplies") == Decimal("9.50")
    assert _money(shown, "total") == Decimal("229.50")


def test_capped_at_forty_dollars(fk):
    shown = json.loads(fk("wo", "show", _order(fk, "10"), "--json"))
    assert _money(shown, "supplies") == Decimal("40.00")
    assert _money(shown, "total") == Decimal("1020.00")


def test_no_labour_no_supplies(fk):
    shown = json.loads(fk("wo", "show", _order(fk), "--json"))
    assert _money(shown, "supplies") == 0
    assert _money(shown, "total") == Decimal("30.00")


def test_rounded_to_the_cent(fk):
    shown = json.loads(fk("wo", "show", _order(fk, "1.5"), "--json"))
    assert _money(shown, "labour") == Decimal("142.50")
    assert _money(shown, "supplies") in (Decimal("7.12"), Decimal("7.13"))
    assert _money(shown, "total") == Decimal("172.50") + _money(shown, "supplies")
