from invoicekit import invoice_from_dict, render_text

INVOICE = {
    "number": "P-1", "issued": "2026-09-01", "region": "US-NY", "currency": "USD",
    "lines": [
        {"sku": "W-100", "description": "Widget", "quantity": 3, "unit_price": "19.99", "category": "standard"},
        {"sku": "SV-1", "description": "Installation", "quantity": 4, "unit_price": "45.00", "category": "services"},
    ],
    "discounts": [{"kind": "amount", "amount": "30"}],
}


def test_discount_total_in_parentheses():
    lines = render_text(invoice_from_dict(INVOICE)).splitlines()
    assert any(line.startswith("Discount") and line.rstrip().endswith("($30.00)") for line in lines)


def test_no_minus_signs_on_amounts():
    text = render_text(invoice_from_dict(INVOICE))
    assert "-$" not in text
    assert "($7.50)" in text and "($22.50)" in text


def test_positive_amounts_are_unchanged():
    lines = render_text(invoice_from_dict(INVOICE)).splitlines()
    assert any(line.startswith("Total") and line.rstrip().endswith("$214.63") for line in lines)
    assert any(line.startswith("Subtotal") and line.rstrip().endswith("$239.97") for line in lines)
