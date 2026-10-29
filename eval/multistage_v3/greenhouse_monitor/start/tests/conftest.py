import contextlib
import io
import json

import pytest

from greenhouse.cli.main import main

LAYOUT = {
    "zones": [
        {"id": "gh1", "name": "North house", "crop": "tomato", "valve": "V1",
         "target_moisture": 40, "area_m2": 120, "flow_lpm": 12},
        {"id": "gh2", "name": "South house", "crop": "lettuce", "valve": "V2", "target_moisture": 35},
    ]
}


@pytest.fixture
def data_dir(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "layout.json").write_text(json.dumps(LAYOUT), encoding="utf-8")
    return folder


@pytest.fixture
def cli(data_dir):
    def run(*args, now="2026-05-01T12:00:00"):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--data", str(data_dir), "--now", now, *args])
        return code, out.getvalue(), err.getvalue()

    return run


@pytest.fixture
def export_file(tmp_path):
    """Write a controller export from (time, zone, sensor, kind, value, unit) rows."""
    def write(rows, name="export.csv"):
        path = tmp_path / name
        lines = ["time,zone,sensor,kind,value,unit", *(",".join(row) for row in rows)]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    return write
