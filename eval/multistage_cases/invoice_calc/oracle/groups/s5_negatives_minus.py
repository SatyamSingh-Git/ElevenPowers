import pytest

from invoicekit import invoice_from_dict, render_text

INVOICE = {
    "number": "P-2", "issued": "2026-09-01", "region": "US-NY", "currency": "EUR",
    "lines": [{"sku": "W-100", "description": "Widget", "quantity": 2, "unit_price": "50.00"}],
    "discounts": [{"kind": "percent", "percent": "10"}],
}


def test_minus_keeps_the_old_look():
    text = render_text(invoice_from_dict(INVOICE), negatives="minus")
    assert any(line.startswith("Discount") and line.rstrip().endswith("-€10.00") for line in text.splitlines())
    assert "(€" not in text


def test_parentheses_can_be_asked_for():
    text = render_text(invoice_from_dict(INVOICE), negatives="parentheses")
    assert any(line.startswith("Discount") and line.rstrip().endswith("(€10.00)") for line in text.splitlines())


def test_other_styles_are_refused():
    with pytest.raises(ValueError, match="negatives must be parentheses or minus"):
        render_text(invoice_from_dict(INVOICE), negatives="red")
