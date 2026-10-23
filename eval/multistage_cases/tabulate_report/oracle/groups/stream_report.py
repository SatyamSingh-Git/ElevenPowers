from decimal import Decimal

from tabreport import build_report, render_report

ROWS = [
    {"region": "East", "amount": "1200.50"},
    {"region": "West", "amount": "-150.25"},
    {"region": "East", "amount": "300"},
    {"region": "North", "amount": "1,000.00"},
    {"region": "West", "amount": "99.75"},
]


def _once(rows):
    yield from rows


def test_report_from_a_generator():
    report = build_report(_once(ROWS), ["region"], ["sum:amount", "count", "mean:amount", "max:amount"])
    assert [row[0] for row in report.rows] == ["East", "North", "West"]
    assert report.rows[0][1:] == [Decimal("1500.50"), 2, Decimal("750.25"), Decimal("1200.50")]
    assert report.totals[0] == "TOTAL"
    assert report.totals[1:] == [Decimal("2450.00"), 5, Decimal("490"), Decimal("1200.50")]
    assert report.row_count == 5
    assert render_report(report).splitlines()[-1] == "5 rows"


def test_ungrouped_report_from_a_generator():
    report = build_report(_once(ROWS), [], ["sum:amount", "min:amount"])
    assert report.rows == []
    assert report.totals == [Decimal("2450.00"), Decimal("-150.25")]
    assert report.row_count == 5


def test_generator_is_consumed_exactly_once():
    pulled = []

    def tracked():
        for row in ROWS:
            pulled.append(row)
            yield row

    report = build_report(tracked(), ["region"], ["count"])
    assert len(pulled) == 5
    assert report.totals[-1] == 5
