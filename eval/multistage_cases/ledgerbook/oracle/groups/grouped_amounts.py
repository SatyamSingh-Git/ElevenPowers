import pytest

from ledgerbook import AmountError, format_amount, parse_amount


@pytest.mark.parametrize("minor, currency, text", [
    (123456789, "USD", "1,234,567.89"),
    (-100000, "USD", "-1,000.00"),
    (99999, "USD", "999.99"),
    (-7, "USD", "-0.07"),
    (1234567, "JPY", "1,234,567"),
    (999, "JPY", "999"),
    (12345678, "KWD", "12,345.678"),
])
def test_thousands_are_separated(minor, currency, text):
    assert format_amount(minor, currency) == text


def test_default_currency_groups_too():
    assert format_amount(100000000) == "1,000,000.00"


@pytest.mark.parametrize("text", ["1,234.50", "1,000"])
def test_typed_amounts_stay_strict(text):
    with pytest.raises(AmountError):
        parse_amount(text)
