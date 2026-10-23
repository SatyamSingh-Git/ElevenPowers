from decimal import Decimal

import pytest

from invoicekit.invoice import InvoiceError, compute, invoice_from_dict
from invoicekit.items import ItemError

LINE = {"sku": "W-100", "description": "Widget", "quantity": 3, "unit_price": "19.99"}


def make(**changes):
    return invoice_from_dict({"number": "INV-1", "issued": "2026-03-15", "region": "US-NY", "lines": [LINE],
                              **changes})


def test_defaults():
    invoice = make()
    assert invoice.currency == "USD"
    assert invoice.rounding == "half-up"
    assert invoice.discounts == ()


def test_totals():
    totals = compute(make(lines=[LINE, {**LINE, "sku": "B-1", "unit_price": "25.00", "category": "food"}],
                          discounts=[{"kind": "amount", "amount": "10"}]))
    assert totals.subtotal == Decimal("134.97")
    assert totals.discount == Decimal("10.00")
    assert totals.tax == Decimal("4.93")
    assert totals.total == Decimal("129.90")
    assert sum(line.total for line in totals.lines) == totals.total


@pytest.mark.parametrize("field", ["number", "region", "lines"])
def test_missing_field(field):
    data = {"number": "INV-1", "region": "US-NY", "lines": [LINE]}
    del data[field]
    with pytest.raises(InvoiceError, match=f"invoice missing field: {field}"):
        invoice_from_dict(data)


def test_line_errors_name_the_line():
    with pytest.raises(ItemError, match="line 2: unknown category: toys"):
        make(lines=[LINE, {**LINE, "category": "toys"}])


def test_too_many_lines():
    with pytest.raises(InvoiceError, match="at most 200 line items"):
        make(lines=[LINE] * 201)


def test_no_lines():
    with pytest.raises(InvoiceError, match="at least one line item"):
        make(lines=[])


def test_bad_issue_date():
    with pytest.raises(InvoiceError, match="issue date must be YYYY-MM-DD"):
        make(issued="15/03/2026")


def test_unknown_rounding_mode():
    with pytest.raises(InvoiceError, match="unknown rounding mode: ceiling"):
        make(rounding="ceiling")
