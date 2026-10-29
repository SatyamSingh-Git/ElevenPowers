import json

import pytest

from greenhouse.cli.main import main

LOG = """timestamp,zone,sensor,kind,value,unit
2026-05-01T08:00:00,gh1,GH1-T01,temperature,19.0,C
2026-05-01T11:50:00,gh1,GH1-T01,temperature,31.0,C
2026-05-01T11:50:00,gh1,GH1-S01,soil_moisture,34.0,%
2026-05-01T11:50:00,gh2,GH2-S01,soil_moisture,34.0,%
"""


@pytest.fixture
def logged(data_dir):
    (data_dir / "readings.csv").write_text(LOG)
    return data_dir


def test_now_is_required(data_dir, capsys):
    with pytest.raises(SystemExit):
        main(["--data", str(data_dir), "status"])
    assert "--now is required" in capsys.readouterr().err


def test_ingest_reports_counts_and_problems(cli, export_file):
    path = export_file([
        ("2026-05-01T08:00:00", "gh1", "GH1-T01", "temperature", "21.0", "C"),
        ("2026-05-01T08:00:00", "gh1", "GH1-T02", "temperature", "hot", "C"),
    ])
    code, out, err = cli("ingest", str(path))
    assert code == 0
    assert out.strip() == "imported 1 rows, rejected 1"
    assert err.strip() == "line 3: bad value: hot"


def test_calibrate_sets_shows_and_clears(cli, data_dir):
    assert cli("calibrate", "GH1-T01", "0.5")[1].strip() == "calibrated GH1-T01: +0.50"
    assert json.loads((data_dir / "calibration.json").read_text()) == {"GH1-T01": 0.5}
    assert cli("calibrate", "GH1-T01")[1].strip() == "GH1-T01: +0.50"
    assert cli("calibrate", "GH1-T01", "--clear")[1].strip() == "cleared GH1-T01"
    code, _, err = cli("calibrate", "GH1-T01", "--clear")
    assert code == 1
    assert err.strip() == "error: no offset for GH1-T01"


def test_calibrate_respects_max_offset(cli, data_dir):
    (data_dir / "settings.json").write_text(json.dumps({"max_offset": 2.0}))
    code, _, err = cli("calibrate", "GH1-T01", "3")
    assert code == 1
    assert err.strip() == "error: offset too large: 3.0"


def test_summary_as_json(cli, logged):
    code, out, _ = cli("summary", "--date", "2026-05-01", "--format", "json")
    assert code == 0
    rows = {(r["zone"], r["kind"]): r for r in json.loads(out)["rows"]}
    assert rows[("gh1", "temperature")]["mean"] == 25.0
    assert rows[("gh2", "soil_moisture")]["count"] == 1


def test_check_logs_each_alert_once(cli, logged):
    (logged / "thresholds.json").write_text(json.dumps({"gh1": {"temperature": {"high": 30}}}))
    code, out, _ = cli("check")
    assert code == 0
    assert out.splitlines() == ["gh1 temperature at 31.0 C is above 30.0 C", "1 new alerts"]
    assert cli("check")[1].strip() == "0 new alerts"
    assert cli("alerts")[1].strip() == "12:00 gh1 temperature at 31.0 C is above 30.0 C"


def test_irrigate_writes_the_plan(cli, logged):
    code, out, _ = cli("irrigate")
    assert code == 0
    assert out.splitlines()[0] == "gh1: 12 min (moisture 34.0% below target 40.0%)"
    assert (logged / "irrigation.csv").read_text().splitlines() == [
        "zone,minutes,reason",
        "gh1,12,moisture 34.0% below target 40.0%",
        "gh2,0,moisture 34.0% near target 35.0%",
    ]


def test_record_for_an_unknown_zone_is_an_error(cli):
    code, _, err = cli("record", "GH7-T01", "temperature", "21", "C", "--zone", "gh7")
    assert code == 1
    assert err.strip() == "error: unknown zone: gh7"


def test_validate_finds_cross_file_problems(cli, data_dir):
    (data_dir / "thresholds.json").write_text(json.dumps({"gh5": {"humidity": {"high": 90}}}))
    code, out, _ = cli("validate")
    assert code == 1
    assert out.splitlines() == ["thresholds name unknown zone gh5", "1 problems"]
