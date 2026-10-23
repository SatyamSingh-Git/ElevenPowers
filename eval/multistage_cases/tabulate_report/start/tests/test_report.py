from decimal import Decimal

import pytest

from tabreport import ReportError, build_report, read_csv, render_report

MEASURES = ["sum:amount", "count", "mean:amount"]


def test_rows_in_key_order_with_totals(sales):
    report = build_report(read_csv(sales), ["region"], MEASURES)
    assert report.headers == ["group", "sum(amount)", "count", "mean(amount)"]
    assert [row[0] for row in report.rows] == ["East", "North", "West"]
    assert report.rows[2] == ["West", Decimal("-50.50"), 2, Decimal("-25.25")]
    assert report.totals == ["TOTAL", Decimal("2450.00"), 5, Decimal("490")]
    assert report.row_count == 5


def test_render_plain(sales):
    text = render_report(build_report(read_csv(sales), ["region"], MEASURES))
    assert text == (
        "group  sum(amount)  count  mean(amount)\n"
        "-----  -----------  -----  ------------\n"
        "East     $1,500.50      2       $750.25\n"
        "North    $1,000.00      1     $1,000.00\n"
        "West       -$50.50      2       -$25.25\n"
        "-----  -----------  -----  ------------\n"
        "TOTAL    $2,450.00      5       $490.00\n"
        "\n"
        "5 rows\n"
    )


def test_render_markdown_without_currency(sales):
    report = build_report(read_csv(sales), ["region"], ["sum:amount"], currency=None, totals=False)
    assert render_report(report, "markdown") == (
        "| group | sum(amount) |\n"
        "| ----- | ----------: |\n"
        "| East  |    1,500.50 |\n"
        "| North |    1,000.00 |\n"
        "| West  |      -50.50 |\n"
        "\n"
        "5 rows\n"
    )


def test_sort_by_measure_descending(sales):
    report = build_report(read_csv(sales), ["region"], ["sum:amount"], sort="-sum(amount)")
    assert [row[0] for row in report.rows] == ["East", "North", "West"]
    report = build_report(read_csv(sales), ["region"], ["sum:amount"], sort="sum(amount)")
    assert [row[0] for row in report.rows] == ["West", "North", "East"]


def test_sort_puts_empty_results_last():
    rows = [{"k": "a", "v": ""}, {"k": "b", "v": "1"}, {"k": "c", "v": "5"}]
    report = build_report(rows, ["k"], ["max:v"], sort="-max(v)")
    assert [row[0] for row in report.rows] == ["c", "b", "a"]


def test_no_grouping_gives_only_the_total(sales):
    report = build_report(read_csv(sales), [], ["sum:amount"])
    assert report.rows == []
    assert report.totals == [Decimal("2450.00")]


def test_one_row_footer():
    text = render_report(build_report([{"k": "a", "v": "1"}], ["k"], ["count"]))
    assert text.endswith("\n1 row\n")


@pytest.mark.parametrize("kwargs, message", [
    ({"measures": []}, "at least one measure is needed"),
    ({"currency": "ABC"}, "unknown currency: ABC"),
    ({"sort": "price"}, "unknown sort column: price"),
])
def test_refuses(sales, kwargs, message):
    arguments = {"by": ["region"], "measures": ["count"], **kwargs}
    with pytest.raises(ReportError, match=f"^{message}$"):
        build_report(read_csv(sales), **arguments)
