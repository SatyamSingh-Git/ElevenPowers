"""ERR rows from a controller are kept in the readings log with an empty value and raw."""
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
    export = tmp_path / "export.csv"
    export.write_text("\n".join([
        "time,zone,sensor,kind,value,unit",
        "2026-05-01T08:00:00,gh1,GH1-T01,temperature,20.0,C",
        "2026-05-01T08:10:00,gh1,GH1-T01,temperature,ERR,C",
        "2026-05-01T08:10:00,gh1,GH1-H01,humidity,ERR,%",
        "2026-05-01T08:20:00,gh1,GH1-T01,temperature,21.0,C",
    ]) + "\n", encoding="utf-8")
    assert run(folder, "2026-05-01T08:30:00", "ingest", str(export))[0] == 0
    return folder


def logged(data):
    with (data / "readings.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_every_row_reaches_the_log(data):
    rows = logged(data)
    assert sorted((row["timestamp"], row["sensor"]) for row in rows) == [
        ("2026-05-01T08:00:00", "GH1-T01"),
        ("2026-05-01T08:10:00", "GH1-H01"),
        ("2026-05-01T08:10:00", "GH1-T01"),
        ("2026-05-01T08:20:00", "GH1-T01"),
    ]


def test_err_rows_have_an_empty_value_and_raw(data):
    rows = {(row["timestamp"], row["sensor"]): row for row in logged(data)}
    assert {key: (row["value"], row["raw"]) for key, row in rows.items()} == {
        ("2026-05-01T08:00:00", "GH1-T01"): ("20.0", "20.0"),
        ("2026-05-01T08:10:00", "GH1-T01"): ("", ""),
        ("2026-05-01T08:10:00", "GH1-H01"): ("", ""),
        ("2026-05-01T08:20:00", "GH1-T01"): ("21.0", "21.0"),
    }
    gap = rows[("2026-05-01T08:10:00", "GH1-H01")]
    assert (gap["zone"], gap["kind"]) == ("gh1", "humidity")
