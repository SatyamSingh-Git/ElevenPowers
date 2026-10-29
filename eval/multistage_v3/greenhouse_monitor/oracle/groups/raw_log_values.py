"""The raw column holds the uncalibrated value, in the unit and decimals of value."""
import contextlib
import csv
import io
import json

import pytest

from greenhouse.cli.main import main

LAYOUT = {"zones": [{"id": "gh1", "name": "North house", "crop": "tomato", "valve": "V1"}]}


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
    assert run(folder, "2026-05-01T07:00:00", "calibrate", "GH1-T01", "0.5")[0] == 0
    return folder


def logged(data):
    with (data / "readings.csv").open(newline="", encoding="utf-8") as handle:
        return [(row["sensor"], row["value"], row["raw"]) for row in csv.DictReader(handle)]


def test_imported_rows_keep_the_value_before_calibration(data, tmp_path):
    export = tmp_path / "export.csv"
    export.write_text("\n".join([
        "time,zone,sensor,kind,value,unit",
        "2026-05-01T08:00:00,gh1,GH1-T01,temperature,20.0,C",
        "2026-05-01T09:00:00,gh1,GH1-T01,temperature,68,F",
        "2026-05-01T09:00:00,gh1,GH1-H01,humidity,70,%",
    ]) + "\n", encoding="utf-8")
    assert run(data, "2026-05-01T09:05:00", "ingest", str(export))[0] == 0
    assert logged(data) == [
        ("GH1-T01", "20.5", "20.0"),
        ("GH1-T01", "20.5", "20.0"),
        ("GH1-H01", "70", "70"),
    ]


def test_hand_entered_readings_keep_the_value_before_calibration(data):
    code, _, err = run(data, "2026-05-01T10:00:00", "record", "GH1-T01", "temperature", "21.0", "C", "--zone", "gh1")
    assert code == 0, err
    assert logged(data) == [("GH1-T01", "21.5", "21.0")]
