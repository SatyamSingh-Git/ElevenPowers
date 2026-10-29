"""Controller exports, calibrated, end up in the daily summary."""
import contextlib
import io
import json

import pytest

from greenhouse.cli.main import main

LAYOUT = {"zones": [
    {"id": "gh1", "name": "North house", "crop": "tomato", "valve": "V1", "target_moisture": 40},
    {"id": "gh2", "name": "South house", "crop": "lettuce", "valve": "V2", "target_moisture": 35},
]}

ROWS = [
    "2026-04-30T22:00:00,gh1,gh1-t01,temperature,15.0,C",
    "2026-05-01T08:00:00,gh1,gh1-t01,temperature,20.0,C",
    "2026-05-01T09:00:00,gh1,gh1-t01,temperature,71.6,F",
    "2026-05-01T10:00:00,gh1,gh1-t01,temperature,ERR,C",
    "2026-05-01T11:00:00,gh1,gh1-t01,temperature,24.0,C",
    "2026-05-01T08:00:00,gh1,gh1-h01,humidity,70,%",
    "2026-05-01T10:00:00,gh1,gh1-h01,humidity,80,%",
    "2026-05-01T08:00:00,gh2,gh2-s01,soil_moisture,30.5,%",
    "2026-05-01T08:00:00,gh9,gh9-t01,temperature,20.0,C",
]


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
    export.write_text("\n".join(["time,zone,sensor,kind,value,unit", *ROWS]) + "\n", encoding="utf-8")
    assert run(folder, "2026-05-01T06:00:00", "calibrate", "gh1-t01", "0.5")[0] == 0
    assert run(folder, "2026-05-01T12:00:00", "ingest", str(export))[0] == 0
    return folder


def summary_rows(data, *extra):
    code, out, err = run(data, "2026-05-01T12:00:00", "summary", "--date", "2026-05-01", "--format", "json", *extra)
    assert code == 0, err
    return {(row["zone"], row["kind"]): row for row in json.loads(out)["rows"]}


def test_calibrated_temperatures_are_summarised(data):
    row = summary_rows(data)[("gh1", "temperature")]
    assert (row["count"], row["min"], row["max"], row["mean"]) == (3, 20.5, 24.5, 22.5)
    assert row["unit"] == "C"


def test_every_zone_and_kind_of_the_day_is_summarised(data):
    rows = summary_rows(data)
    assert set(rows) == {("gh1", "temperature"), ("gh1", "humidity"), ("gh2", "soil_moisture")}
    humidity = rows[("gh1", "humidity")]
    assert (humidity["count"], humidity["min"], humidity["max"], humidity["mean"]) == (2, 70, 80, 75)
    assert rows[("gh2", "soil_moisture")]["mean"] == 30.5


def test_the_previous_day_is_summarised_on_its_own(data):
    code, out, _ = run(data, "2026-05-01T12:00:00", "summary", "--date", "2026-04-30", "--format", "json")
    assert code == 0
    (row,) = json.loads(out)["rows"]
    assert (row["zone"], row["kind"], row["count"], row["mean"]) == ("gh1", "temperature", 1, 15.5)
