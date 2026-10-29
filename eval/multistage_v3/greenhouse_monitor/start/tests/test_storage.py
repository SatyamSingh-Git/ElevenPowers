from datetime import date, datetime

import pytest

from greenhouse.core.errors import ValidationError
from greenhouse.core.model import Reading
from greenhouse.storage.archive import archive_readings
from greenhouse.storage.calibration import CalibrationStore, load_calibration
from greenhouse.storage.history import latest_by_sensor, load_readings
from greenhouse.storage.readings_log import ReadingsLog

LOG = """timestamp,zone,sensor,kind,value,unit
2026-04-30T23:50:00,gh1,GH1-T01,temperature,17.5,C
2026-05-01T08:00:00,gh1,GH1-T01,temperature,19.0,C
2026-05-01T08:00:00,gh2,GH2-H01,humidity,72,%
2026-05-01T09:00:00,gh1,GH1-T01,temperature,21.5,C
"""


def reading(**changes):
    values = dict(at=datetime(2026, 5, 1, 8, 0), zone="gh1", sensor="GH1-T01", kind="temperature",
                  value=21.04, unit="C", raw=20.54)
    return Reading(**{**values, **changes})


def test_log_starts_with_column_names_and_rounds_values(tmp_path):
    log = ReadingsLog(tmp_path / "readings.csv")
    assert log.write_many([reading(), reading(kind="humidity", value=70.6, unit="%")]) == 2
    assert (tmp_path / "readings.csv").read_text().splitlines() == [
        "timestamp,zone,sensor,kind,value,unit",
        "2026-05-01T08:00:00,gh1,GH1-T01,temperature,21.0,C",
        "2026-05-01T08:00:00,gh1,GH1-T01,humidity,71,%",
    ]


def test_log_is_appended_without_repeating_column_names(tmp_path):
    log = ReadingsLog(tmp_path / "readings.csv")
    log.write(reading())
    log.write(reading(at=datetime(2026, 5, 1, 9, 0)))
    lines = (tmp_path / "readings.csv").read_text().splitlines()
    assert len(lines) == 3
    assert lines[2].startswith("2026-05-01T09:00:00,")


def test_history_loads_the_log_in_order(tmp_path):
    (tmp_path / "readings.csv").write_text(LOG)
    readings = load_readings(tmp_path / "readings.csv")
    assert [r.value for r in readings] == [17.5, 19.0, 72.0, 21.5]
    assert readings[2].sensor == "GH2-H01"


def test_history_filters_by_day_and_zone(tmp_path):
    (tmp_path / "readings.csv").write_text(LOG)
    day = load_readings(tmp_path / "readings.csv", day=date(2026, 5, 1))
    assert len(day) == 3
    zone = load_readings(tmp_path / "readings.csv", day=date(2026, 5, 1), zone="gh1")
    assert [r.value for r in zone] == [19.0, 21.5]


def test_history_of_a_missing_log_is_empty(tmp_path):
    assert load_readings(tmp_path / "readings.csv") == []


def test_latest_reading_per_sensor(tmp_path):
    (tmp_path / "readings.csv").write_text(LOG)
    latest = latest_by_sensor(load_readings(tmp_path / "readings.csv"))
    assert sorted(latest) == ["GH1-T01", "GH2-H01"]
    assert latest["GH1-T01"].value == 21.5


def test_uncalibrated_sensor_reads_zero(tmp_path):
    assert load_calibration(tmp_path / "calibration.json").offset_for("GH1-T01") == 0.0


def test_offsets_survive_a_save(tmp_path):
    store = load_calibration(tmp_path / "calibration.json")
    store.set_offset("GH1-T01", 0.5, 5.0)
    store.save()
    assert load_calibration(tmp_path / "calibration.json").items() == [("GH1-T01", 0.5)]


def test_offset_above_the_limit_is_refused(tmp_path):
    store = CalibrationStore(tmp_path / "calibration.json")
    with pytest.raises(ValidationError, match="offset too large: 6.5"):
        store.set_offset("GH1-T01", 6.5, 5.0)


def test_clearing_an_offset(tmp_path):
    store = CalibrationStore(tmp_path / "calibration.json", {"GH1-T01": 0.5})
    assert store.clear("GH1-T01")
    assert not store.clear("GH1-T01")


def test_archive_moves_old_rows_by_month(tmp_path):
    (tmp_path / "readings.csv").write_text(LOG)
    moved = archive_readings(tmp_path / "readings.csv", tmp_path / "archive", date(2026, 5, 1))
    assert moved == {"2026-04": 1}
    archived = (tmp_path / "archive" / "readings-2026-04.csv").read_text().splitlines()
    assert archived == ["timestamp,zone,sensor,kind,value,unit", "2026-04-30T23:50:00,gh1,GH1-T01,temperature,17.5,C"]
    assert len((tmp_path / "readings.csv").read_text().splitlines()) == 4
