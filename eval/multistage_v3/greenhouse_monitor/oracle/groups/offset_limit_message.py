"""An offset outside max_offset in either direction gets the out-of-range message."""
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


def test_positive_offset_beyond_the_limit(data):
    code, _, err = run(data, NOW, "calibrate", "GH1-T01", "7")
    assert code != 0
    assert "offset out of range: 7.0 (limit 5.0)" in err


def test_the_message_names_the_site_limit(data):
    (data / "settings.json").write_text(json.dumps({"max_offset": 10}), encoding="utf-8")
    code, _, err = run(data, NOW, "calibrate", "GH1-T01", "-12")
    assert code != 0
    assert "offset out of range: -12.0 (limit 10.0)" in err
    code, _, err = run(data, NOW, "calibrate", "GH1-T01", "-9.5")
    assert code == 0, err
