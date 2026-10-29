"""summary --zone with a zone missing from the layout fails with the unknown zone error."""
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


def test_unknown_zone(data):
    code, _, err = run(data, "2026-05-01T12:00:00", "summary", "--zone", "gh9")
    assert code != 0
    assert "unknown zone: gh9" in err


def test_unknown_zone_in_text_format_too(data):
    code, _, err = run(data, "2026-05-01T12:00:00", "summary", "--zone", "nursery", "--format", "text")
    assert code != 0
    assert "unknown zone: nursery" in err
