from decimal import Decimal

from tabreport import aggregate, build_report, read_csv

SALES = """region,product,units,amount
East,Widget,3,1200.50
West,Gadget,1,-150.25
East,Gadget,2,300
North,Widget,5,"1,000.00"
West,Widget,4,99.75
"""


def _rows(tmp_path):
    path = tmp_path / "sales.csv"
    path.write_bytes(SALES.encode("utf-8"))
    return list(read_csv(path))


def test_aggregate_returns_each_key_under_its_column(tmp_path):
    results = aggregate(_rows(tmp_path), ["region", "product"], ["sum:amount", "count"])
    first = results[0]
    assert first["region"] == "East" and first["product"] == "Widget"
    assert "group" not in first
    assert len(results) == 5
    assert {(r["region"], r["product"]) for r in results} == {
        ("East", "Widget"), ("West", "Gadget"), ("East", "Gadget"), ("North", "Widget"), ("West", "Widget")}


def test_single_key_column_is_named_after_the_csv_column(tmp_path):
    report = build_report(_rows(tmp_path), ["product"], ["sum:amount"])
    assert report.headers[0] == "product"
    assert [row[0] for row in report.rows] == ["Gadget", "Widget"]


def test_two_key_columns_sorted_with_blank_key_in_totals(tmp_path):
    report = build_report(_rows(tmp_path), ["region", "product"], ["sum:amount", "count"])
    assert report.headers[:2] == ["region", "product"]
    assert len(report.headers) == 4
    assert [tuple(row[:2]) for row in report.rows] == [
        ("East", "Gadget"), ("East", "Widget"), ("North", "Widget"), ("West", "Gadget"), ("West", "Widget")]
    assert report.rows[1][2:] == [Decimal("1200.50"), 1]
    assert report.totals[0] == "TOTAL"
    assert report.totals[1] in ("", None)
    assert report.totals[2:] == [Decimal("2450.00"), 5]
