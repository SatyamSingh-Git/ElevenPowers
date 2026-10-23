import pytest

from invoicekit import compute, invoice_from_dict

INVOICE = {"number": "N-1", "region": "US-NY", "currency": "USD",
           "lines": [{"sku": "W-1", "description": "Widget", "quantity": 1, "unit_price": "5.00"}]}


def test_missing_issue_date_is_refused():
    with pytest.raises(ValueError, match="invoice issue date is required"):
        invoice_from_dict(INVOICE)


def test_issue_date_given_is_accepted():
    assert compute(invoice_from_dict({**INVOICE, "issued": "2026-02-02"})).subtotal == 5
