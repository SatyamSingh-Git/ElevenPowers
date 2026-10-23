import pytest

from ledgerbook import AmountError, format_amount, parse_amount


@pytest.mark.parametrize("text, currency, minor", [
    ("12.50", "USD", 1250),
    ("12.5", "USD", 1250),
    ("-0.07", "USD", -7),
    ("3", "USD", 300),
    ("500", "JPY", 500),
    ("1.250", "KWD", 1250),
])
def test_parse_amount(text, currency, minor):
    assert parse_amount(text, currency) == minor


@pytest.mark.parametrize("text", ["", "abc", "1.", ".5", "1,000.00", "+3"])
def test_parse_amount_rejects_malformed_text(text):
    with pytest.raises(AmountError, match="invalid amount"):
        parse_amount(text)


def test_parse_amount_rejects_extra_precision():
    with pytest.raises(AmountError, match="too many decimal places for USD: 1.005"):
        parse_amount("1.005", "USD")
    with pytest.raises(AmountError, match="too many decimal places for JPY"):
        parse_amount("1.5", "JPY")


@pytest.mark.parametrize("minor, currency, text", [
    (1250, "USD", "12.50"),
    (-7, "USD", "-0.07"),
    (0, "USD", "0.00"),
    (500, "JPY", "500"),
    (1250, "KWD", "1.250"),
])
def test_format_amount(minor, currency, text):
    assert format_amount(minor, currency) == text


def test_unknown_currency():
    with pytest.raises(AmountError, match="unknown currency: XXX"):
        format_amount(1, "XXX")
