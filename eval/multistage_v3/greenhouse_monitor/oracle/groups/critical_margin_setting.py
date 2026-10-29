"""The critical_margin setting in settings.json moves the line between warning and critical."""
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
    (folder / "thresholds.json").write_text(json.dumps({"gh1": {"temperature": {"low": 10, "high": 30}}}))
    return folder


def check(data, tmp_path, *readings):
    export = tmp_path / "export.csv"
    rows = [f"2026-05-01T11:50:00,gh1,{sensor},temperature,{value},C" for sensor, value in readings]
    export.write_text("\n".join(["time,zone,sensor,kind,value,unit", *rows]) + "\n", encoding="utf-8")
    assert run(data, "2026-05-01T11:55:00", "ingest", str(export))[0] == 0
    code, _, err = run(data, "2026-05-01T12:00:00", "check")
    assert code == 0, err
    lines = (data / "alerts.jsonl").read_text(encoding="utf-8").splitlines()
    return {record["sensor"].upper(): record["code"] for record in map(json.loads, filter(None, lines))}


def test_a_wider_margin(data, tmp_path):
    (data / "settings.json").write_text(json.dumps({"critical_margin": 10}), encoding="utf-8")
    codes = check(data, tmp_path, ("GH1-T01", 36.0), ("GH1-T02", 41.0), ("GH1-T03", 4.0), ("GH1-T04", -1.0))
    assert codes == {"GH1-T01": "high", "GH1-T02": "critical_high", "GH1-T03": "low", "GH1-T04": "critical_low"}


def test_a_narrower_margin(data, tmp_path):
    (data / "settings.json").write_text(json.dumps({"critical_margin": 1.5}), encoding="utf-8")
    codes = check(data, tmp_path, ("GH1-T01", 31.0), ("GH1-T02", 32.0))
    assert codes == {"GH1-T01": "high", "GH1-T02": "critical_high"}
