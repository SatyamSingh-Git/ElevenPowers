"""summary --zone limits the summary to one zone; all, the default, lists every zone."""
import contextlib
import io
import json

import pytest

from greenhouse.cli.main import main

LAYOUT = {"zones": [
    {"id": "gh1", "name": "North house", "crop": "tomato", "valve": "V1"},
    {"id": "gh2", "name": "South house", "crop": "lettuce", "valve": "V2"},
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
        "2026-05-01T08:00:00,gh1,GH1-T01,temperature,20.0,C",
        "2026-05-01T09:00:00,gh1,GH1-T01,temperature,22.0,C",
        "2026-05-01T08:00:00,gh2,GH2-T01,temperature,18.0,C",
        "2026-05-01T08:00:00,gh2,GH2-H01,humidity,75,%",
    ]) + "\n", encoding="utf-8")
    assert run(folder, "2026-05-01T09:10:00", "ingest", str(export))[0] == 0
    return folder


def summary(data, *extra):
    code, out, err = run(data, "2026-05-01T12:00:00", "summary", "--date", "2026-05-01", "--format", "json", *extra)
    assert code == 0, err
    return sorted((row["zone"], row["kind"], row["mean"]) for row in json.loads(out)["rows"])


def test_one_zone(data):
    assert summary(data, "--zone", "gh2") == [("gh2", "humidity", 75), ("gh2", "temperature", 18.0)]
    assert summary(data, "--zone", "gh1") == [("gh1", "temperature", 21.0)]


def test_all_zones_by_default_and_by_name(data):
    every = [("gh1", "temperature", 21.0), ("gh2", "humidity", 75), ("gh2", "temperature", 18.0)]
    assert summary(data) == every
    assert summary(data, "--zone", "all") == every
