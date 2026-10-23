import re
from decimal import Decimal

import pytest

from invoicekit import compute, invoice_from_dict, render_text

LINES = [
    {"sku": "F-1", "description": "Coffee beans", "quantity": 10, "unit_price": "1.00", "category": "food"},
    {"sku": "B-1", "description": "Novel", "quantity": 1, "unit_price": "20.00", "category": "books"},
    {"sku": "S-1", "description": "Grinder", "quantity": 1, "unit_price": "10.00", "category": "standard"},
]


def german(issued):
    return invoice_from_dict({"number": "DE-9", "issued": issued, "region": "DE", "currency": "EUR", "lines": LINES})


@pytest.mark.parametrize("issued, taxes", [
    ("2026-12-31", ["0.70", "1.40", "1.90"]),
    ("2027-01-01", ["0.90", "1.80", "1.90"]),
    ("2028-07-15", ["0.90", "1.80", "1.90"]),
])
def test_reduced_rate_follows_the_issue_date(issued, taxes):
    totals = compute(german(issued))
    assert [line.tax for line in totals.lines] == [Decimal(tax) for tax in taxes]
    assert totals.total == Decimal("40.00") + sum(Decimal(tax) for tax in taxes)


def test_printed_invoice_shows_the_rate_in_force():
    late = render_text(german("2027-03-01"))
    assert re.search(r"(?<![\d.])9%", late)
    assert not re.search(r"(?<![\d.])7%", late)
    early = render_text(german("2026-03-01"))
    assert re.search(r"(?<![\d.])7%", early)
    assert not re.search(r"(?<![\d.])9%", early)


def test_other_regions_are_unchanged():
    totals = compute(invoice_from_dict({"number": "JP-1", "issued": "2027-03-01", "region": "JP", "currency": "JPY",
                                        "lines": [{"sku": "F-1", "description": "Rice", "quantity": 1,
                                                   "unit_price": "1000", "category": "food"}]}))
    assert totals.tax == Decimal(80)
