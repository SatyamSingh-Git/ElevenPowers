from datetime import date
import json

import pytest

from fleetkeep.cli.main import main
from fleetkeep.clock import FixedClock


@pytest.fixture
def run(tmp_path, capsys):
    def run(*args):
        code = main(["--fleet", str(tmp_path / "fleet"), *args], clock=FixedClock(date(2026, 3, 1)))
        out, err = capsys.readouterr()
        return code, out, err
    run("init", "--name", "North")
    run("vehicle", "add", "van-101", "--class", "light", "--make", "Ford", "--model", "Transit",
        "--year", "2025", "--in-service", "2025-09-01", "--odometer", "100")
    return run


def test_work_order_from_the_command_line(run):
    assert run("odometer", "add", "VAN-101", "5900", "--on", "2026-02-20")[0] == 0
    code, out, _ = run("wo", "open", "VAN-101", "--service", "TIRE-ROT")
    assert (code, out) == (0, "WO-0001\n")
    run("wo", "part", "WO-0001", "--number", "VS-4", "--price", "4.25", "--qty", "4")
    run("wo", "close", "wo-0001")
    shown = json.loads(run("wo", "show", "WO-0001", "--json")[1])
    assert (shown["status"], shown["closed"], shown["parts"], shown["total"]) == (
        "closed", "2026-03-01", "17.00", "17.00")


def test_due_as_csv(run):
    run("odometer", "add", "VAN-101", "6300", "--on", "2026-02-20")
    _, out, _ = run("due", "--format", "csv", "--as-of", "2026-02-20")
    lines = out.splitlines()
    assert lines[0] == "vehicle,code,service,due_miles,remaining_miles,due_date,remaining_days,status"
    assert lines[1] == "VAN-101,TIRE-ROT,Tyre rotation,6100,-200,,,overdue"
    assert lines[2] == "VAN-101,OIL,Engine oil and filter,7600,1300,2026-03-01,9,due-soon"


def test_errors_exit_with_one(run):
    code, out, err = run("odometer", "add", "VAN-999", "100")
    assert (code, out) == (1, "")
    assert err == "error: E103 unknown vehicle: VAN-999\n"
