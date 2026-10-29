"""Closing a closed work order fails with E126."""
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
    fk("vehicle", "add", "VAN-801", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    return fk


def test_second_close_fails(fk):
    order = fk("wo", "open", "VAN-801", "--service", "OIL", "--on", "2026-02-02")[1].strip()
    assert fk("wo", "close", order, "--on", "2026-02-03")[0] == 0
    code, out, err = fk("wo", "close", order, "--on", "2026-02-10")
    assert code == 1
    assert "E126" in err
    assert f"work order {order} is already closed" in err


def test_open_orders_still_close(fk):
    order = fk("wo", "open", "VAN-801", "--on", "2026-02-02")[1].strip()
    assert fk("wo", "close", order, "--on", "2026-02-03")[0] == 0
