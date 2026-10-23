from decimal import Decimal

import pytest

from tabreport import Measure, ReportError, aggregate, parse_measure, read_csv


def test_parse_measure():
    assert parse_measure("sum:amount") == Measure("sum", "amount")
    assert parse_measure(" MEAN : units ") == Measure("mean", "units")
    assert parse_measure("count") == Measure("count")


@pytest.mark.parametrize("spec, message", [
    ("median:amount", "unknown measure: median"),
    ("sum", "measure needs a column: sum"),
    ("count:amount", "count takes no column"),
])
def test_parse_measure_refuses(spec, message):
    with pytest.raises(ReportError, match=f"^{message}$"):
        parse_measure(spec)


def test_labels():
    assert Measure("sum", "amount").label == "sum(amount)"
    assert Measure("count").label == "count"


def test_aggregate_by_one_column(sales):
    results = aggregate(read_csv(sales), ["region"], ["sum:amount", "count", "mean:amount"])
    assert [r["group"] for r in results] == ["East", "West", "North"]
    east = results[0]
    assert east["sum(amount)"] == Decimal("1500.50")
    assert east["count"] == 2
    assert east["mean(amount)"] == Decimal("750.25")


def test_aggregate_by_two_columns(sales):
    results = aggregate(read_csv(sales), ["region", "product"], ["min:amount", "max:units"])
    assert results[0] == {"group": "East / Widget", "min(amount)": Decimal("1200.50"),
                          "max(units)": Decimal("3")}
    assert len(results) == 5


def test_blank_cells_are_skipped_but_counted():
    rows = [{"k": "a", "v": "2"}, {"k": "a", "v": ""}, {"k": "b", "v": " "}]
    results = aggregate(rows, ["k"], ["count", "mean:v", "min:v"])
    assert results[0] == {"group": "a", "count": 2, "mean(v)": Decimal("2"), "min(v)": Decimal("2")}
    assert results[1] == {"group": "b", "count": 1, "mean(v)": None, "min(v)": None}


def test_bad_number_stops_the_aggregate():
    with pytest.raises(ReportError, match="^not a number: 'lots'$"):
        aggregate([{"k": "a", "v": "lots"}], ["k"], ["sum:v"])


def test_missing_column_in_row():
    with pytest.raises(ReportError, match="^missing column: k$"):
        aggregate([{"v": "1"}], ["k"], ["sum:v"])
