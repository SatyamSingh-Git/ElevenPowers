"""Day-to-day operation: hand-entered readings, alerts in the report, and the valve schedule."""
import contextlib
import io
import json

import pytest

from greenhouse.cli.main import main

LAYOUT = {"zones": [
    {"id": "gh1", "name": "North house", "crop": "tomato", "valve": "V1", "target_moisture": 40},
    {"id": "gh2", "name": "South house", "crop": "lettuce", "valve": "V2", "target_moisture": 35},
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
    return folder


def ingest(data, tmp_path, now, *rows):
    export = tmp_path / "export.csv"
    export.write_text("\n".join(["time,zone,sensor,kind,value,unit", *rows]) + "\n", encoding="utf-8")
    code, _, err = run(data, now, "ingest", str(export))
    assert code == 0, err


def test_hand_entered_reading_becomes_the_sensors_latest(data, tmp_path):
    ingest(data, tmp_path, "2026-05-01T10:05:00", "2026-05-01T10:00:00,gh1,gh1-t01,temperature,21.0,C")
    code, _, err = run(data, "2026-05-01T11:00:00", "record", "gh1-t01", "temperature", "23.5", "C", "--zone", "gh1")
    assert code == 0, err
    code, out, _ = run(data, "2026-05-01T11:00:00", "status", "--format", "json")
    assert code == 0
    rows = [row for row in json.loads(out) if row["zone"] == "gh1" and row["kind"] == "temperature"]
    assert len(rows) == 1
    assert rows[0]["value"] == 23.5
    assert rows[0]["sensor"].lower() == "gh1-t01"


def test_alert_is_listed_and_reported(data, tmp_path):
    (data / "thresholds.json").write_text(json.dumps({"gh1": {"temperature": {"low": 10, "high": 30}}}))
    ingest(data, tmp_path, "2026-05-01T11:55:00",
           "2026-05-01T11:50:00,gh1,gh1-t02,temperature,36.0,C",
           "2026-05-01T11:50:00,gh1,gh1-t03,temperature,20.0,C")
    code, out, _ = run(data, "2026-05-01T12:00:00", "check")
    assert code == 0
    assert "36.0" in out
    code, out, _ = run(data, "2026-05-01T12:30:00", "alerts", "--date", "2026-05-01")
    assert code == 0
    (line,) = [line for line in out.splitlines() if line.strip()]
    assert "gh1" in line and "36.0" in line
    code, out, _ = run(data, "2026-05-01T20:00:00", "report", "--date", "2026-05-01")
    assert code == 0
    assert any("gh1" in line and "36.0" in line for line in out.splitlines())


def test_irrigation_plan_becomes_the_valve_schedule(data, tmp_path):
    ingest(data, tmp_path, "2026-05-01T06:10:00", "2026-05-01T06:00:00,gh1,gh1-s01,soil_moisture,35.0,%")
    code, _, err = run(data, "2026-05-01T06:30:00", "irrigate")
    assert code == 0, err
    code, out, err = run(data, "2026-05-01T06:30:00", "schedule")
    assert code == 0, err
    assert (data / "valves.txt").read_text(encoding="utf-8").splitlines() == ["06:00 V1 gh1 10"]
