import pytest

from invoicekit import invoice_from_dict, render_text

INVOICE = {
    "number": "N-5", "issued": "2026-09-01", "region": "US-NY", "currency": "USD",
    "lines": [{"sku": "W-100", "description": "Widget", "quantity": 1, "unit_price": "5.00"}],
}


def test_long_notes_are_refused():
    with pytest.raises(ValueError, match="notes must be at most 500 characters"):
        invoice_from_dict({**INVOICE, "notes": "word " * 101})


def test_notes_at_the_limit_are_accepted():
    notes = ("abcd " * 100)[:499] + "z"
    assert len(notes) == 500
    assert "z" in render_text(invoice_from_dict({**INVOICE, "notes": notes})).split()[-1]
