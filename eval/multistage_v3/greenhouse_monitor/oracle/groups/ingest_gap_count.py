"""ingest counts ERR rows as gaps, neither imported nor rejected."""
import contextlib
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
    return folder


def ingest(data, tmp_path, *rows):
    export = tmp_path / "export.csv"
    export.write_text("\n".join(["time,zone,sensor,kind,value,unit", *rows]) + "\n", encoding="utf-8")
    return run(data, "2026-05-01T09:00:00", "ingest", str(export))


def test_the_printed_counts(data, tmp_path):
    code, out, _ = ingest(
        data, tmp_path,
        "2026-05-01T08:00:00,gh1,GH1-T01,temperature,20.0,C",
        "2026-05-01T08:10:00,gh1,GH1-T01,temperature,ERR,C",
        "2026-05-01T08:20:00,gh1,GH1-T01,temperature,21.0,C",
        "2026-05-01T08:20:00,gh9,GH9-T01,temperature,21.0,C",
    )
    assert code == 0
    assert out.strip() == "imported 2 rows, 1 gaps, rejected 1"


def test_a_file_of_gaps_only(data, tmp_path):
    code, out, _ = ingest(
        data, tmp_path,
        "2026-05-01T08:00:00,gh1,GH1-T01,temperature,ERR,C",
        "2026-05-01T08:10:00,gh1,GH1-H01,humidity,ERR,%",
    )
    assert code == 0
    assert out.strip() == "imported 0 rows, 2 gaps, rejected 0"
