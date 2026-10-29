"""Irrigation suggestions round up to whole five-minute timer steps by default."""
import contextlib
import csv
import io
import json

import pytest

from greenhouse.cli.main import main

LAYOUT = {"zones": [
    {"id": "gh1", "name": "North house", "crop": "tomato", "valve": "V1", "target_moisture": 40},
    {"id": "gh2", "name": "South house", "crop": "lettuce", "valve": "V2", "target_moisture": 35},
    {"id": "gh3", "name": "House three", "crop": "pepper", "valve": "V3", "target_moisture": 50},
    {"id": "gh4", "name": "Propagation", "crop": "basil", "valve": "V4", "target_moisture": 40},
]}


def run(data, now, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(["--data", str(data), "--now", now, *args])
        except SystemExit as stop:
            code = stop.code
    return code, out.getvalue(), err.getvalue()


@pytest.fixture
def data(tmp_path):
    folder = tmp_path / "site"
    folder.mkdir()
    (folder / "layout.json").write_text(json.dumps(LAYOUT), encoding="utf-8")
    export = tmp_path / "export.csv"
    export.write_text("\n".join([
        "time,zone,sensor,kind,value,unit",
        "2026-05-01T06:00:00,gh1,GH1-S01,soil_moisture,34.0,%",
        "2026-05-01T06:00:00,gh2,GH2-S01,soil_moisture,34.0,%",
        "2026-05-01T06:00:00,gh3,GH3-S01,soil_moisture,38.0,%",
        "2026-05-01T06:00:00,gh4,GH4-S01,soil_moisture,35.0,%",
    ]) + "\n", encoding="utf-8")
    assert run(folder, "2026-05-01T06:10:00", "ingest", str(export))[0] == 0
    return folder


def planned(data):
    with (data / "irrigation.csv").open(newline="", encoding="utf-8") as handle:
        return {row["zone"]: int(row["minutes"]) for row in csv.DictReader(handle)}


def test_suggestions_are_whole_timer_steps(data):
    code, out, err = run(data, "2026-05-01T06:30:00", "irrigate")
    assert code == 0, err
    assert planned(data) == {"gh1": 15, "gh2": 0, "gh3": 25, "gh4": 10}
    assert "gh1: 15 min" in out


def test_the_valve_schedule_uses_the_rounded_minutes(data):
    assert run(data, "2026-05-01T06:30:00", "irrigate")[0] == 0
    code, _, err = run(data, "2026-05-01T06:30:00", "schedule")
    assert code == 0, err
    assert (data / "valves.txt").read_text(encoding="utf-8").splitlines() == [
        "06:00 V1 gh1 15",
        "06:15 V3 gh3 25",
        "06:40 V4 gh4 10",
    ]
