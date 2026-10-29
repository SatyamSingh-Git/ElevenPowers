"""The timer_step_minutes setting in settings.json sets the step suggestions round up to."""
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
        "2026-05-01T06:00:00,gh3,GH3-S01,soil_moisture,43.5,%",
    ]) + "\n", encoding="utf-8")
    assert run(folder, "2026-05-01T06:10:00", "ingest", str(export))[0] == 0
    return folder


def planned(data, step):
    (data / "settings.json").write_text(json.dumps({"timer_step_minutes": step}), encoding="utf-8")
    code, _, err = run(data, "2026-05-01T06:30:00", "irrigate")
    assert code == 0, err
    with (data / "irrigation.csv").open(newline="", encoding="utf-8") as handle:
        return {row["zone"]: int(row["minutes"]) for row in csv.DictReader(handle)}


def test_a_ten_minute_step(data):
    assert planned(data, 10) == {"gh1": 20, "gh2": 0, "gh3": 20}


def test_a_one_minute_step_keeps_the_exact_minutes(data):
    assert planned(data, 1) == {"gh1": 12, "gh2": 0, "gh3": 13}
