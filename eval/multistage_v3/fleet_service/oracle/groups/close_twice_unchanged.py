"""A refused second close leaves the work order, its history and its downtime as they were."""
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
        return code, out

    fk("init", "--name", "North")
    fk("vehicle", "add", "VAN-802", "--class", "light", "--make", "Ford", "--model", "Transit",
       "--year", "2025", "--in-service", "2025-10-01", "--odometer", "0")
    fk("odometer", "add", "VAN-802", "3000", "--on", "2026-02-01")
    order = fk("wo", "open", "VAN-802", "--service", "OIL", "--on", "2026-02-02")[1].strip()
    fk("wo", "close", order, "--on", "2026-02-04")
    fk("wo", "close", order, "--on", "2026-02-20")
    fk.order = order
    return fk


def test_close_date_kept(fk):
    shown = json.loads(fk("wo", "show", fk.order, "--json")[1])
    assert (shown["status"], shown["closed"]) == ("closed", "2026-02-04")


def test_services_recorded_once(fk):
    history = fk("history", "show", "VAN-802", "--format", "csv")[1].splitlines()
    assert history[1:] == [f"2026-02-04,OIL,Engine oil and filter,3000,{fk.order}"]


def test_downtime_kept(fk):
    rows = json.loads(fk("downtime", "--from", "2026-02-01", "--to", "2026-02-28",
                         "--format", "json")[1])
    assert rows[0]["days_down"] == 2
