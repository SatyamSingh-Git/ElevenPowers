"""The readings log carries a raw column right after value."""
import contextlib
import io
import json

import pytest

from greenhouse.cli.main import main

LAYOUT = {"zones": [{"id": "gh1", "name": "North house", "crop": "tomato", "valve": "V1"}]}
COLUMNS = "timestamp,zone,sensor,kind,value,raw,unit"


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


def test_an_import_starts_the_log_with_the_new_columns(data, tmp_path):
    export = tmp_path / "export.csv"
    export.write_text("time,zone,sensor,kind,value,unit\n2026-05-01T08:00:00,gh1,GH1-T01,temperature,20.0,C\n",
                      encoding="utf-8")
    assert run(data, "2026-05-01T08:05:00", "ingest", str(export))[0] == 0
    lines = (data / "readings.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == COLUMNS
    assert len(lines[1].split(",")) == 7


def test_a_hand_entered_reading_starts_the_log_with_the_new_columns(data):
    code, _, err = run(data, "2026-05-01T08:05:00", "record", "GH1-T01", "temperature", "20.0", "C", "--zone", "gh1")
    assert code == 0, err
    lines = (data / "readings.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == COLUMNS
    assert len(lines) == 2
