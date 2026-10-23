from decimal import Decimal

import pytest

from tabreport import ReportError, format_money, format_number, parse_amount


@pytest.mark.parametrize("text, expected", [
    ("12", "12"),
    (" 1,234.50 ", "1234.50"),
    ("-$12", "-12"),
    ("(7.25)", "-7.25"),
    ("CHF 3", "3"),
    ("€1,000", "1000"),
    ("+4.5", "4.5"),
])
def test_parse_amount(text, expected):
    assert parse_amount(text) == Decimal(expected)


@pytest.mark.parametrize("text", ["abc", "", "1.2.3", "NaN", "$"])
def test_parse_amount_refuses(text):
    with pytest.raises(ReportError, match="^not a number: "):
        parse_amount(text)


def test_parse_amount_other_separator():
    assert parse_amount("1.234", thousands=".") == Decimal("1234")


def test_format_number_rounds_half_up():
    assert format_number(Decimal("2.345")) == "2.35"
    assert format_number(Decimal("-2.345")) == "-2.35"
    assert format_number(Decimal("0.5"), 0) == "1"


def test_format_number_groups_thousands():
    assert format_number(Decimal("1234567.891")) == "1,234,567.89"
    assert format_number(Decimal("999.999")) == "1,000.00"
    assert format_number(1234, 0, thousands=" ") == "1 234"
    assert format_number(Decimal("-0.001")) == "0.00"


def test_format_money():
    assert format_money(Decimal("1234.5")) == "$1,234.50"
    assert format_money(Decimal("-50.5"), "eur") == "-€50.50"
    assert format_money(Decimal("1234.5"), "JPY") == "¥1,235"
    assert format_money(Decimal("1.2345"), "KWD") == "KD 1.235"


def test_format_money_unknown_currency():
    with pytest.raises(ReportError, match="^unknown currency: XYZ$"):
        format_money(1, "XYZ")
