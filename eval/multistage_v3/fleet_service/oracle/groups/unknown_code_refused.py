"""Opening a work order for a service the catalog lacks fails with E127."""
from datetime import date
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
        return code, out, err

    fk("init", "--name", "North")
    fk("vehicle", "add", "VAN-101", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    return fk


def test_unknown_code_fails(fk):
    code, _, err = fk("wo", "open", "VAN-101", "--service", "OIL2", "--on", "2026-02-02")
    assert code == 1
    assert "E127" in err
    assert "unknown service code: OIL2" in err


def test_no_order_is_created(fk):
    fk("wo", "open", "VAN-101", "--service", "OIL2", "--on", "2026-02-02")
    assert json.loads(fk("wo", "list", "--format", "json")[1]) == []
