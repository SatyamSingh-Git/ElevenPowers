from datetime import datetime

import pytest

from greenhouse.config.layout import load_layout
from greenhouse.core.errors import ConfigError, ValidationError
from greenhouse.services.ingest import ingest_file
from greenhouse.services.manual import record_manual
from greenhouse.storage.calibration import CalibrationStore
from greenhouse.storage.readings_log import ReadingsLog


@pytest.fixture
def layout(data_dir):
    return load_layout(data_dir / "layout.json")


@pytest.fixture
def log(tmp_path):
    return ReadingsLog(tmp_path / "readings.csv")


def logged(log):
    return log.path.read_text().splitlines()[1:]


def test_rows_are_converted_calibrated_and_logged(export_file, log, layout, tmp_path):
    calibration = CalibrationStore(tmp_path / "calibration.json", {"GH1-T01": 0.5})
    path = export_file([
        ("2026-05-01T08:00:00", "gh1", "GH1-T01", "temperature", "68", "F"),
        ("2026-05-01T08:00:00", "gh1", "GH1-L01", "light", "21.5", "klux"),
    ])
    result = ingest_file(path, log, layout, calibration)
    assert (result.imported, result.rejected) == (2, 0)
    assert logged(log) == [
        "2026-05-01T08:00:00,gh1,GH1-T01,temperature,20.5,C",
        "2026-05-01T08:00:00,gh1,GH1-L01,light,21500,lux",
    ]


def test_bad_rows_are_reported_by_line_and_the_rest_logged(export_file, log, layout, tmp_path):
    path = export_file([
        ("2026-05-01T08:00:00", "gh1", "GH1-T01", "temperature", "21.0", "C"),
        ("2026-05-01T08:00:00", "gh9", "GH9-T01", "temperature", "21.0", "C"),
        ("2026-05-01T08:00:00", "gh1", "GH1-T02", "temperature", "warm", "C"),
        ("2026-05-01T08:00:00", "gh1", "GH1-T03", "temperature", "21.0", "K"),
        ("2026-05-01T08:00:00", "gh1", "GH1-S01", "soil_moisture", "120", "%"),
        ("2026-05-01T08:00:00", "gh1", "", "temperature", "21.0", "C"),
        ("01/05/2026 08:00", "gh1", "GH1-T04", "temperature", "21.0", "C"),
        ("2026-05-01T08:00:00", "gh1", "GH1-T01", "temperature", "21.5", "C"),
    ])
    result = ingest_file(path, log, layout, CalibrationStore(tmp_path / "calibration.json"))
    assert (result.imported, result.rejected) == (1, 7)
    assert result.problems == [
        "line 3: unknown zone: gh9",
        "line 4: bad value: warm",
        "line 5: unknown unit K for temperature",
        "line 6: out of range: 120.0 %",
        "line 7: missing sensor",
        "line 8: bad time: 01/05/2026 08:00",
        "line 9: duplicate reading for GH1-T01",
    ]
    assert len(logged(log)) == 1


def test_export_without_the_expected_columns_is_refused(tmp_path, log, layout):
    path = tmp_path / "export.csv"
    path.write_text("time,sensor,value\n2026-05-01T08:00:00,GH1-T01,21\n")
    with pytest.raises(ValidationError, match="export.csv: expected columns time,zone,sensor,kind,value,unit"):
        ingest_file(path, log, layout, CalibrationStore(tmp_path / "calibration.json"))


def test_manual_reading_is_calibrated_and_logged(log, layout, tmp_path):
    calibration = CalibrationStore(tmp_path / "calibration.json", {"GH2-S01": -1.0})
    reading = record_manual(log, layout, calibration, zone="gh2", sensor="GH2-S01", kind="soil_moisture",
                            value=31.0, unit="%", at=datetime(2026, 5, 1, 10, 30))
    assert reading.value == 30.0
    assert logged(log) == ["2026-05-01T10:30:00,gh2,GH2-S01,soil_moisture,30.0,%"]


def test_light_cannot_be_entered_by_hand(log, layout, tmp_path):
    with pytest.raises(ValidationError, match="light cannot be entered by hand"):
        record_manual(log, layout, CalibrationStore(tmp_path / "calibration.json"), zone="gh1",
                      sensor="GH1-L01", kind="light", value=20000, unit="lux", at=datetime(2026, 5, 1))


def test_manual_reading_for_an_unknown_zone_is_refused(log, layout, tmp_path):
    with pytest.raises(ConfigError, match="unknown zone: gh7"):
        record_manual(log, layout, CalibrationStore(tmp_path / "calibration.json"), zone="gh7",
                      sensor="GH7-T01", kind="temperature", value=20, unit="C", at=datetime(2026, 5, 1))
