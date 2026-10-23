from decimal import Decimal

from tabreport import format_money, format_number


def test_plain_numbers_are_not_grouped_by_default():
    assert format_number(Decimal("12500")) == "12500.00"
    assert format_number(Decimal("1234567.891"), 1) == "1234567.9"
    assert format_number(1204, 0) == "1204"
    assert format_number(Decimal("-98765.4321")) == "-98765.43"


def test_grouping_still_available_on_request():
    assert format_number(Decimal("1234567.891"), thousands=",") == "1,234,567.89"
    assert format_number(1204, 0, thousands=" ") == "1 204"


def test_money_keeps_its_separators():
    assert format_money(Decimal("12500")) == "$12,500.00"
    assert format_money(Decimal("-1234567.5"), "JPY") == "-¥1,234,568"
    assert format_money(Decimal("1000"), "GBP") == "£1,000.00"
