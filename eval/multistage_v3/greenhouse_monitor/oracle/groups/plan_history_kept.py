"""irrigate keeps earlier days' plans and replaces only its own day's rows."""
import contextlib
import csv
import io
import json

import pytest

from greenhouse.cli.main import main

LAYOUT = {"zones": [{"id": "gh1", "name": "North house", "crop": "tomato", "valve": "V1", "target_moisture": 40}]}


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


def irrigate_after(data, tmp_path, at, moisture):
    export = tmp_path / "export.csv"
    export.write_text(f"time,zone,sensor,kind,value,unit\n{at},gh1,GH1-S01,soil_moisture,{moisture},%\n",
                      encoding="utf-8")
    assert run(data, at, "ingest", str(export))[0] == 0
    code, _, err = run(data, at, "irrigate")
    assert code == 0, err


def plans(data):
    lines = (data / "irrigation.csv").read_text(encoding="utf-8").splitlines()
    assert lines.count("date,zone,minutes,reason") == 1
    with (data / "irrigation.csv").open(newline="", encoding="utf-8") as handle:
        return sorted((row["date"], row["zone"], row["minutes"]) for row in csv.DictReader(handle))


def test_earlier_days_are_kept(data, tmp_path):
    irrigate_after(data, tmp_path, "2026-05-01T06:00:00", "35.0")
    irrigate_after(data, tmp_path, "2026-05-02T06:00:00", "30.0")
    assert plans(data) == [("2026-05-01", "gh1", "10"), ("2026-05-02", "gh1", "20")]


def test_a_second_run_on_the_same_day_replaces_that_day(data, tmp_path):
    irrigate_after(data, tmp_path, "2026-05-01T06:00:00", "35.0")
    irrigate_after(data, tmp_path, "2026-05-02T06:00:00", "30.0")
    irrigate_after(data, tmp_path, "2026-05-02T09:00:00", "36.0")
    assert plans(data) == [("2026-05-01", "gh1", "10"), ("2026-05-02", "gh1", "10")]
