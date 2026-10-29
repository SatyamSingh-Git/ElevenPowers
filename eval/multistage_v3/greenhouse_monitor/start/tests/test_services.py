from datetime import date, datetime

import pytest

from greenhouse.config.layout import load_layout
from greenhouse.config.settings import Settings
from greenhouse.config.thresholds import Thresholds
from greenhouse.core.errors import ValidationError
from greenhouse.core.model import Limits, Reading
from greenhouse.services.alerts import evaluate, unreported
from greenhouse.services.climate import vapour_pressure_deficit, zone_climate
from greenhouse.services.irrigation import suggest
from greenhouse.services.light import daily_light
from greenhouse.services.summary import hourly_means, mean_changes, summarize
from greenhouse.services.trends import trends
from greenhouse.services.uptime import find_gaps, uptime
from greenhouse.services.valves import build_schedule

NOON = datetime(2026, 5, 1, 12, 0)


def reading(sensor, kind, value, at=NOON, zone="gh1"):
    unit = {"temperature": "C", "light": "lux"}.get(kind, "%")
    return Reading(at=at, zone=zone, sensor=sensor, kind=kind, value=value, unit=unit)


def test_summary_per_zone_and_kind():
    stats = summarize([
        reading("GH1-T01", "temperature", 20.0),
        reading("GH1-T02", "temperature", 23.0),
        reading("GH1-T01", "temperature", 21.5),
        reading("GH2-H01", "humidity", 70.0, zone="gh2"),
    ])
    assert [(s.zone, s.kind, s.count, s.low, s.high, s.mean) for s in stats] == [
        ("gh1", "temperature", 3, 20.0, 23.0, 21.5),
        ("gh2", "humidity", 1, 70.0, 70.0, 70.0),
    ]


def test_mean_changes_against_the_previous_day():
    today = summarize([reading("GH1-T01", "temperature", 22.0)])
    before = summarize([reading("GH1-T01", "temperature", 20.5), reading("GH2-H01", "humidity", 70.0, zone="gh2")])
    assert mean_changes(today, before) == {("gh1", "temperature"): 1.5}


def test_hourly_means_group_by_the_hour():
    means = hourly_means([
        reading("GH1-L01", "light", 1000, at=datetime(2026, 5, 1, 9, 10)),
        reading("GH1-L01", "light", 3000, at=datetime(2026, 5, 1, 9, 50)),
    ])
    assert means == {("gh1", "light", datetime(2026, 5, 1, 9, 0)): 2000}


def test_limit_and_stale_alerts():
    thresholds = Thresholds({"gh1": {"temperature": Limits(low=10.0, high=30.0)}})
    latest = {
        "GH1-T01": reading("GH1-T01", "temperature", 31.0),
        "GH1-T02": reading("GH1-T02", "temperature", 9.5),
        "GH1-T03": reading("GH1-T03", "temperature", 20.0),
        "GH1-T04": reading("GH1-T04", "temperature", 45.0, at=datetime(2026, 5, 1, 11, 0)),
    }
    alerts = evaluate(latest, thresholds, Settings(), NOON)
    assert [(a.sensor, a.code, a.limit) for a in alerts] == [
        ("GH1-T01", "high", 30.0),
        ("GH1-T02", "low", 10.0),
        ("GH1-T04", "stale", 30),
    ]


def test_alerts_already_logged_today_are_not_repeated():
    thresholds = Thresholds({"gh1": {"temperature": Limits(high=30.0)}})
    alerts = evaluate({"GH1-T01": reading("GH1-T01", "temperature", 31.0)}, thresholds, Settings(), NOON)
    assert unreported(alerts, {(date(2026, 5, 1), "GH1-T01", "high")}) == []
    assert unreported(alerts, {(date(2026, 4, 30), "GH1-T01", "high")}) == alerts


@pytest.fixture
def layout(data_dir):
    return load_layout(data_dir / "layout.json")


def test_irrigation_follows_the_driest_probe(layout):
    latest = {
        "GH1-S01": reading("GH1-S01", "soil_moisture", 36.0),
        "GH1-S02": reading("GH1-S02", "soil_moisture", 34.0),
        "GH2-S01": reading("GH2-S01", "soil_moisture", 34.0, zone="gh2"),
    }
    suggestions = suggest(layout, latest, Settings())
    assert [(s.zone, s.minutes) for s in suggestions] == [("gh1", 12), ("gh2", 0)]
    assert suggestions[0].reason == "moisture 34.0% below target 40.0%"


def test_irrigation_is_capped(layout):
    latest = {"GH1-S01": reading("GH1-S01", "soil_moisture", 10.0)}
    assert suggest(layout, latest, Settings())[0].minutes == 30


def test_zone_without_a_probe_gets_no_water(layout):
    assert suggest(layout, {}, Settings())[0].reason == "no soil moisture reading"


def test_valves_run_back_to_back(layout):
    lines = build_schedule([("gh1", 12), ("gh2", 5)], layout, (6, 0))
    assert lines == ["06:00 V1 gh1 12", "06:12 V2 gh2 5"]


def test_schedule_may_not_run_past_midnight(layout):
    with pytest.raises(ValidationError, match="past midnight"):
        build_schedule([("gh1", 30)], layout, (23, 45))


def test_light_integral_and_photoperiod():
    readings = [reading("GH1-L01", "light", 20000, at=datetime(2026, 5, 1, hour)) for hour in range(8, 18)]
    readings.append(reading("GH1-L01", "light", 2000, at=datetime(2026, 5, 1, 19)))
    (light,) = daily_light(readings, Settings())
    assert light.photoperiod == 10
    assert light.hours_measured == 11
    assert light.dli == pytest.approx(13.45, abs=0.01)


def test_vapour_pressure_deficit():
    assert vapour_pressure_deficit(25.0, 60.0) == pytest.approx(1.27, abs=0.01)
    stats = summarize([reading("GH1-T01", "temperature", 25.0), reading("GH1-H01", "humidity", 95.0)])
    (climate,) = zone_climate(stats, Settings())
    assert climate.band == "low"


def test_uptime_counts_gaps_longer_than_the_setting():
    readings = [reading("GH1-T01", "temperature", 20.0, at=datetime(2026, 5, 1, 0, m)) for m in (5, 15, 25)]
    readings.append(reading("GH1-T01", "temperature", 20.0, at=datetime(2026, 5, 1, 1, 25)))
    gaps = find_gaps(readings, date(2026, 5, 1), 20, datetime(2026, 5, 1, 1, 30))
    assert [(g.start.strftime("%H:%M"), g.minutes) for g in gaps] == [("00:25", 60)]
    assert uptime(gaps, {"GH1-T01"}, date(2026, 5, 1), datetime(2026, 5, 1, 1, 30)) == {"GH1-T01": 33.3}


def test_trend_is_the_slope_per_hour():
    readings = [reading("GH1-T01", "temperature", 20.0 + n, at=datetime(2026, 5, 1, 9 + n)) for n in range(3)]
    (trend,) = trends(readings, NOON, 4)
    assert trend.per_hour == 1.0
    assert trend.direction == "rising"
