"""Sensor ids reach the readings log in upper case, however they were spelled."""
import contextlib
import csv
import io
import json

import pytest

from greenhouse.cli.main import main

LAYOUT = {"zones": [{"id": "gh3", "name": "House three", "crop": "pepper", "valve": "V3"}]}


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


def logged_sensors(data):
    with (data / "readings.csv").open(newline="", encoding="utf-8") as handle:
        return [row["sensor"] for row in csv.DictReader(handle)]


def test_imported_ids_are_logged_in_upper_case(data, tmp_path):
    export = tmp_path / "export.csv"
    export.write_text("\n".join([
        "time,zone,sensor,kind,value,unit",
        "2026-05-01T08:00:00,gh3,gh3-t01,temperature,20.0,C",
        "2026-05-01T08:00:00,gh3,Gh3-T02,temperature,20.5,C",
        "2026-05-01T08:00:00,gh3,GH3-H01,humidity,70,%",
    ]) + "\n", encoding="utf-8")
    assert run(data, "2026-05-01T08:05:00", "ingest", str(export))[0] == 0
    assert logged_sensors(data) == ["GH3-T01", "GH3-T02", "GH3-H01"]


def test_hand_entered_ids_are_logged_in_upper_case(data):
    code, _, err = run(data, "2026-05-01T09:00:00", "record", "gh3-s01", "soil_moisture", "31.0", "%", "--zone", "gh3")
    assert code == 0, err
    assert logged_sensors(data) == ["GH3-S01"]
