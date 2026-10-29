"""One unknown code among known ones refuses the whole order; known codes still open orders."""
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
    fk("vehicle", "add", "TRK-102", "--class", "heavy", "--make", "Volvo", "--model", "VNL",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    return fk


def test_mixed_codes_are_refused(fk):
    code, _, err = fk("wo", "open", "TRK-102", "--service", "OIL", "--service", "BRAKES",
                      "--service", "DPF", "--on", "2026-02-02")
    assert code == 1
    assert "unknown service code: BRAKES" in err
    assert json.loads(fk("wo", "list", "--format", "json")[1]) == []


def test_known_codes_open_and_close(fk):
    fk("wo", "open", "TRK-102", "--service", "OIL", "--service", "BRAKES", "--on", "2026-02-02")
    code, out, _ = fk("wo", "open", "TRK-102", "--service", "OIL", "--service", "DPF",
                      "--on", "2026-02-02")
    assert code == 0
    order = out.strip()
    assert fk("wo", "close", order, "--on", "2026-02-03")[0] == 0
    history = fk("history", "show", "TRK-102", "--format", "json")[1]
    assert [row["code"] for row in json.loads(history)] == ["DPF", "OIL"]
