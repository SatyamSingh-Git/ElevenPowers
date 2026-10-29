"""calibrate refuses negative offsets beyond max_offset, and keeps accepting those within it."""
import contextlib
import io
import json

import pytest

from greenhouse.cli.main import main

LAYOUT = {"zones": [{"id": "gh1", "name": "North house", "crop": "tomato", "valve": "V1"}]}
NOW = "2026-05-01T07:00:00"


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


def saved(data):
    path = data / "calibration.json"
    if not path.exists():
        return {}
    return {sensor.upper(): offset for sensor, offset in json.loads(path.read_text(encoding="utf-8")).items()}


def test_negative_offset_beyond_the_limit_is_refused(data):
    code, _, err = run(data, NOW, "calibrate", "GH1-T01", "-12")
    assert code != 0
    assert "offset out of range: -12.0 (limit 5.0)" in err
    assert "GH1-T01" not in saved(data)


def test_negative_offsets_within_the_limit_are_kept(data):
    assert run(data, NOW, "calibrate", "GH1-T01", "-4.5")[0] == 0
    assert run(data, NOW, "calibrate", "GH1-T02", "-5")[0] == 0
    assert saved(data) == {"GH1-T01": -4.5, "GH1-T02": -5.0}
