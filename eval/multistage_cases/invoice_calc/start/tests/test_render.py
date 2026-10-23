import pytest

from invoicekit.invoice import invoice_from_dict
from invoicekit.render import render_text

INVOICE = {
    "number": "INV-7", "issued": "2026-03-15", "region": "US-NY",
    "lines": [
        {"sku": "W-100", "description": "Widget", "quantity": 3, "unit_price": "19.99"},
        {"sku": "SV-1", "description": "Installation", "quantity": 1, "unit_price": "45.00", "category": "services"},
    ],
    "discounts": [{"kind": "amount", "amount": "5"}],
}


def test_render_text():
    text = render_text(invoice_from_dict(INVOICE))
    lines = text.splitlines()
    assert lines[0] == "INVOICE INV-7"
    assert "Issued: 2026-03-15" in lines[1]
    assert any(line.startswith("W-100") and line.endswith("$59.97") for line in lines)
    assert lines[-1].startswith("Total") and lines[-1].endswith("$105.04")
    assert any(line.startswith("Discount") and line.endswith("-$5.00") for line in lines)
    assert any(line.startswith("Tax 8.875% on $57.11") for line in lines)
    assert all(len(line) <= 64 for line in lines)


def test_render_width():
    text = render_text(invoice_from_dict(INVOICE), width=80)
    assert max(len(line) for line in text.splitlines()) == 80


def test_render_width_minimum():
    with pytest.raises(ValueError, match="width must be at least 56"):
        render_text(invoice_from_dict(INVOICE), width=40)
