"""Labour on heavy vehicles is charged at the heavy rate unless `--rate` is given."""
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
    fk("vehicle", "add", "TRK-301", "--class", "heavy", "--make", "Volvo", "--model", "VNL",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk("vehicle", "add", "VAN-301", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk("vehicle", "add", "BOX-301", "--class", "medium", "--make", "Isuzu", "--model", "NPR",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    return fk


def _labour(fk, vehicle, *rate):
    order = fk("wo", "open", vehicle, "--on", "2026-02-02").strip()
    fk("wo", "labour", order, "--mechanic", "Ana", "--hours", "2", *rate)
    return Decimal(str(json.loads(fk("wo", "show", order, "--json"))["labour"]))


def test_heavy_rate(fk):
    assert _labour(fk, "TRK-301") == Decimal("250.00")


def test_other_classes_keep_the_labour_rate(fk):
    assert _labour(fk, "VAN-301") == Decimal("190.00")
    assert _labour(fk, "BOX-301") == Decimal("190.00")


def test_explicit_rate_wins(fk):
    assert _labour(fk, "TRK-301", "--rate", "100.00") == Decimal("200.00")
