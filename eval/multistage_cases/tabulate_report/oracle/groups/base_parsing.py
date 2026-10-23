from decimal import Decimal

import pytest

from tabreport import Dialect, ReportError, format_money, format_number, parse_amount, read_csv


def _write(tmp_path, text, name="data.csv"):
    path = tmp_path / name
    path.write_bytes(text.encode("utf-8"))
    return path


def test_semicolon_dialect_keeps_quoted_delimiter(tmp_path):
    path = _write(tmp_path, 'name;note\n"Smith; J";late\n')
    assert list(read_csv(path, Dialect(delimiter=";"))) == [{"name": "Smith; J", "note": "late"}]


def test_header_and_cells_stripped_and_blank_lines_skipped(tmp_path):
    path = _write(tmp_path, " a , b \n 1 , x \n\n2,y\n")
    assert list(read_csv(path)) == [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}]


def test_missing_required_column(tmp_path):
    path = _write(tmp_path, "region,amount\nEast,1\n")
    with pytest.raises(ReportError, match="^missing column: price$"):
        list(read_csv(path, required=["region", "price"]))


def test_field_count_names_the_line(tmp_path):
    path = _write(tmp_path, "a,b\n1,2\n3\n")
    with pytest.raises(ReportError, match="^wrong field count: line 3 has 1, expected 2$"):
        list(read_csv(path))


@pytest.mark.parametrize("text, expected", [
    ("1,234.50", "1234.50"),
    ("(7.25)", "-7.25"),
    ("-$12", "-12"),
    ("€1,000", "1000"),
    ("12", "12"),
])
def test_parse_amount(text, expected):
    assert parse_amount(text) == Decimal(expected)


def test_parse_amount_refuses_text():
    with pytest.raises(ReportError, match="^not a number: 'abc'$"):
        parse_amount("abc")


def test_format_number_with_explicit_grouping():
    assert format_number(Decimal("-1234.565"), 2, thousands=",") == "-1,234.57"
    assert format_number(Decimal("2.345"), 2, thousands=",") == "2.35"
    assert format_number(Decimal("0.5"), 0, thousands=",") == "1"


def test_format_money():
    assert format_money(Decimal("1234.5")) == "$1,234.50"
    assert format_money(Decimal("-50.5"), "EUR") == "-€50.50"
    assert format_money(Decimal("1234.5"), "JPY") == "¥1,235"
    assert format_money(Decimal("1234567.891"), "usd") == "$1,234,567.89"


def test_unknown_currency():
    with pytest.raises(ReportError, match="^unknown currency: XYZ$"):
        format_money(Decimal(1), "XYZ")
