from decimal import Decimal
import re

import pytest

from tabreport import ReportError, parse_amount


@pytest.mark.parametrize("text", ["12,34", "1,2345", ",123", "1.234,5", "-$1,00", "(1,23)"])
def test_misplaced_separator_is_refused(text):
    with pytest.raises(ReportError, match=f"^misplaced thousands separator: {re.escape(repr(text))}$"):
        parse_amount(text)


@pytest.mark.parametrize("text, expected", [
    ("1,234", "1234"),
    ("12,345,678.90", "12345678.90"),
    ("$1,000", "1000"),
    ("(1,000.50)", "-1000.50"),
    ("999", "999"),
    ("1234567.5", "1234567.5"),
    ("-12,345", "-12345"),
])
def test_well_grouped_amounts_still_parse(text, expected):
    assert parse_amount(text) == Decimal(expected)
