from decimal import Decimal

import pytest

from invoicekit.tax import TaxError, format_rate, line_tax, normalize_region, rate_for


def test_rates_by_region_and_category():
    assert rate_for("standard", "US-NY") == Decimal("8.875")
    assert rate_for("food", "DE") == Decimal(7)
    assert rate_for("food", "JP") == Decimal(8)


def test_region_codes_are_case_insensitive():
    assert normalize_region(" de ") == "DE"


def test_unknown_region():
    with pytest.raises(TaxError, match="unknown region: FR"):
        rate_for("standard", "FR")


def test_line_tax_is_rounded_to_the_currency():
    assert line_tax(Decimal("59.97"), "standard", "US-NY", "USD", "half-up") == Decimal("5.32")
    assert line_tax(Decimal("1233"), "food", "JP", "JPY", "half-up") == Decimal("99")


def test_format_rate():
    assert format_rate(Decimal("8.875")) == "8.875%"
    assert format_rate(Decimal("10")) == "10%"
