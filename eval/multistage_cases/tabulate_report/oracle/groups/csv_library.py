import csv
from decimal import Decimal
import io

from tabreport import build_report, render_report, render_table

ROWS = [
    {"region": "East", "amount": "1200.50"},
    {"region": "West", "amount": "-150.25"},
    {"region": "East", "amount": "300"},
    {"region": "North", "amount": "1,000.00"},
    {"region": "West", "amount": "99.75"},
]


def _parse(text):
    return [row for row in csv.reader(io.StringIO(text)) if row]


def test_report_as_csv_with_bare_amounts():
    report = build_report(ROWS, ["region"], ["sum:amount", "count", "mean:amount"])
    rows = _parse(render_report(report, "csv"))
    assert rows[0][0] == "region" and len(rows[0]) == 4
    assert rows[1:] == [
        ["East", "1500.50", "2", "750.25"],
        ["North", "1000.00", "1", "1000.00"],
        ["West", "-50.50", "2", "-25.25"],
        ["TOTAL", "2450.00", "5", "490.00"],
    ]


def test_csv_follows_currency_decimals():
    report = build_report(ROWS, ["region"], ["sum:amount"], currency="KWD", totals=False)
    rows = _parse(render_report(report, "csv"))
    assert [row[1] for row in rows[1:]] == ["1500.500", "1000.000", "-50.500"]
    assert len(rows) == 4


def test_render_table_csv_quotes_cells():
    text = render_table(["name", "amount"], [["Smith, J", "$1,000.00"], ["Lee", None]], "csv")
    assert _parse(text) == [["name", "amount"], ["Smith, J", "$1,000.00"], ["Lee", ""]]
    assert Decimal(_parse(render_report(build_report(ROWS, [], ["sum:amount"]), "csv"))[-1][0]) == Decimal("2450")
