"""`critical_miles` and `critical_days` in fleet.ini move the critical margin."""
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
        assert code == 0, err
        return out

    fk("init", "--name", "North")
    fk("vehicle", "add", "VAN-601", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk.ini = root / "fleet.ini"
    return fk


def _status(fk, as_of, code):
    rows = json.loads(fk("due", "--as-of", as_of, "--format", "json", "--vehicle", "VAN-601"))
    return next(row["status"] for row in rows if row["code"] == code)


def test_wider_mileage_margin(fk):
    fk.ini.write_text("[fleet]\nname = North\ncritical_miles = 2000\n", encoding="utf-8")
    fk("odometer", "add", "VAN-601", "9000", "--on", "2026-02-20")
    assert _status(fk, "2026-02-21", "OIL") == "overdue"
    fk("odometer", "add", "VAN-601", "9501", "--on", "2026-02-25")
    assert _status(fk, "2026-02-26", "OIL") == "critical"


def test_narrower_days_margin(fk):
    fk.ini.write_text("[fleet]\nname = North\ncritical_days = 7\n", encoding="utf-8")
    assert _status(fk, "2026-04-08", "OIL") == "overdue"
    assert _status(fk, "2026-04-09", "OIL") == "critical"


def test_defaults_without_the_settings(fk):
    fk.ini.write_text("[fleet]\nname = North\n", encoding="utf-8")
    fk("odometer", "add", "VAN-601", "8600", "--on", "2026-02-20")
    assert _status(fk, "2026-02-21", "OIL") == "critical"
