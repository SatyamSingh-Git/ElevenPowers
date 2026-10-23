from decimal import Decimal

from invoicekit import compute, invoice_from_dict


def test_mixed_uk_invoice_taxes_only_standard_lines():
    totals = compute(invoice_from_dict({
        "number": "UK-2", "issued": "2026-06-01", "region": "gb", "currency": "GBP",
        "lines": [
            {"sku": "S-1", "description": "Kettle", "quantity": 2, "unit_price": "15.00", "category": "standard"},
            {"sku": "F-1", "description": "Tea", "quantity": 3, "unit_price": "4.00", "category": "food"},
            {"sku": "B-1", "description": "Cookbook", "quantity": 1, "unit_price": "8.00", "category": "books"},
        ],
        "discounts": [{"kind": "percent", "percent": "10"}],
    }))
    assert [line.tax for line in totals.lines] == [Decimal("5.40"), Decimal(0), Decimal(0)]
    assert (totals.subtotal, totals.discount, totals.tax, totals.total) == (
        Decimal("50.00"), Decimal("5.00"), Decimal("5.40"), Decimal("50.40"))
