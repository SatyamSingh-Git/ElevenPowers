"""irrigation.csv starts with the plan's date: date,zone,minutes,reason."""
import contextlib
import csv
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
    export = tmp_path / "export.csv"
    export.write_text("\n".join([
        "time,zone,sensor,kind,value,unit",
        "2026-05-01T06:00:00,gh1,GH1-S01,soil_moisture,35.0,%",
        "2026-05-01T06:00:00,gh2,GH2-S01,soil_moisture,34.0,%",
    ]) + "\n", encoding="utf-8")
    assert run(folder, "2026-05-01T06:10:00", "ingest", str(export))[0] == 0
    return folder


def test_columns_start_with_the_date(data):
    assert run(data, "2026-05-01T07:00:00", "irrigate")[0] == 0
    first = (data / "irrigation.csv").read_text(encoding="utf-8").splitlines()[0]
    assert first == "date,zone,minutes,reason"


def test_rows_carry_the_day_irrigate_ran(data):
    assert run(data, "2026-05-01T07:00:00", "irrigate")[0] == 0
    with (data / "irrigation.csv").open(newline="", encoding="utf-8") as handle:
        rows = [(row["date"], row["zone"], row["minutes"]) for row in csv.DictReader(handle)]
    assert rows == [("2026-05-01", "gh1", "10"), ("2026-05-01", "gh2", "0")]
