import json
from datetime import date

import pytest

from greenhouse.core.errors import ValidationError
from greenhouse.core.model import DailyStats
from greenhouse.reports.charts import sparkline
from greenhouse.reports.export import render_summary
from greenhouse.reports.messages import describe

DAY = date(2026, 5, 1)
STATS = [DailyStats("gh1", "temperature", "C", 3, 20.0, 23.0, 21.5)]


def test_summary_as_json():
    data = json.loads(render_summary("json", DAY, STATS))
    assert data == {"date": "2026-05-01", "rows": [
        {"zone": "gh1", "kind": "temperature", "unit": "C", "count": 3, "min": 20.0, "max": 23.0, "mean": 21.5}
    ]}


def test_summary_as_csv():
    assert render_summary("csv", DAY, STATS).splitlines() == [
        "date,zone,kind,unit,count,min,max,mean",
        "2026-05-01,gh1,temperature,C,3,20.0,23.0,21.5",
    ]


def test_summary_as_text_lines_up_columns():
    lines = render_summary("text", DAY, STATS).splitlines()
    assert lines[0] == "Summary for 2026-05-01"
    assert lines[2].split() == ["zone", "kind", "count", "min", "max", "mean", "unit"]
    assert lines[3].split() == ["gh1", "temperature", "3", "20.0", "23.0", "21.5", "C"]


def test_unknown_summary_format():
    with pytest.raises(ValidationError, match="unknown format: xml"):
        render_summary("xml", DAY, STATS)


def test_alert_descriptions():
    high = {"at": "2026-05-01T12:00:00", "zone": "gh1", "sensor": "GH1-T01", "kind": "temperature",
            "code": "high", "value": 31.0, "limit": 30.0, "unit": "C"}
    assert describe(high) == "gh1 temperature at 31.0 C is above 30.0 C"
    stale = {**high, "code": "stale", "limit": 30}
    assert describe(stale) == "gh1 sensor GH1-T01 has not reported for 30 minutes"
    dry = {**high, "kind": "soil_moisture", "code": "low", "value": 21.0, "limit": 25.0, "unit": "%"}
    assert describe(dry) == "gh1 soil moisture at 21.0 % is below 25.0 %"


def test_sparkline_scales_between_lowest_and_highest():
    assert sparkline([1.0, None, 4.0, 2.5]) == " .#="
    assert sparkline([None, None]) == ".."
