"""Two spellings of one sensor id are one sensor."""
import contextlib
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


def ingest(data, tmp_path, name, now, *rows):
    export = tmp_path / name
    export.write_text("\n".join(["time,zone,sensor,kind,value,unit", *rows]) + "\n", encoding="utf-8")
    code, _, err = run(data, now, "ingest", str(export))
    assert code == 0, err


def test_old_and_new_controllers_report_one_sensor(data, tmp_path):
    ingest(data, tmp_path, "old.csv", "2026-05-01T10:05:00", "2026-05-01T10:00:00,gh3,gh3-t01,temperature,21.0,C")
    ingest(data, tmp_path, "new.csv", "2026-05-01T11:05:00", "2026-05-01T11:00:00,gh3,GH3-T01,temperature,22.0,C")
    code, out, _ = run(data, "2026-05-01T11:10:00", "status", "--format", "json")
    assert code == 0
    (row,) = json.loads(out)
    assert (row["sensor"], row["value"]) == ("GH3-T01", 22.0)


def test_hand_entered_spelling_is_the_same_sensor(data, tmp_path):
    ingest(data, tmp_path, "new.csv", "2026-05-01T10:05:00", "2026-05-01T10:00:00,gh3,GH3-T01,temperature,21.0,C")
    code, _, err = run(data, "2026-05-01T11:00:00", "record", "Gh3-t01", "temperature", "23.0", "C", "--zone", "gh3")
    assert code == 0, err
    code, out, _ = run(data, "2026-05-01T11:10:00", "status", "--format", "json")
    assert code == 0
    (row,) = json.loads(out)
    assert (row["sensor"], row["value"]) == ("GH3-T01", 23.0)
