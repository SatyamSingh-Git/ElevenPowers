from decimal import Decimal

import pytest

from invoicekit.money import MoneyError, format_money, quantize, to_decimal


def test_format_money_groups_thousands():
    assert format_money(Decimal("1234.5"), "USD") == "$1,234.50"


def test_format_money_uses_the_currency_minor_units():
    assert format_money(Decimal("1234.5"), "JPY") == "¥1,235"
    assert format_money(Decimal("1.2345"), "KWD") == "KD 1.235"


def test_format_money_puts_the_sign_before_the_symbol():
    assert format_money(Decimal("-12"), "EUR") == "-€12.00"


def test_quantize_rounding_modes():
    assert quantize(Decimal("2.345"), "USD") == Decimal("2.35")
    assert quantize(Decimal("2.345"), "USD", "half-even") == Decimal("2.34")
    assert quantize(Decimal("2.349"), "USD", "down") == Decimal("2.34")


def test_to_decimal_refuses_floats():
    with pytest.raises(MoneyError, match="not float"):
        to_decimal(0.1)


def test_to_decimal_refuses_text_that_is_not_a_number():
    with pytest.raises(MoneyError, match="not a number"):
        to_decimal("12,50")


def test_unknown_currency():
    with pytest.raises(MoneyError, match="unknown currency: XXX"):
        format_money(Decimal(1), "XXX")
