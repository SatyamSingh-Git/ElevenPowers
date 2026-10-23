from decimal import Decimal

from invoicekit import compute, invoice_from_dict


def uk(*lines):
    return compute(invoice_from_dict({"number": "UK-1", "issued": "2026-06-01", "region": "GB", "currency": "GBP",
                                      "lines": list(lines)}))


def test_food_carries_no_tax():
    totals = uk({"sku": "F-1", "description": "Biscuits", "quantity": 4, "unit_price": "2.50", "category": "food"})
    assert totals.tax == Decimal(0)
    assert totals.total == Decimal("10.00")


def test_books_carry_no_tax():
    totals = uk({"sku": "B-1", "description": "Atlas", "quantity": 1, "unit_price": "12.99", "category": "books"})
    assert totals.tax == Decimal(0)
    assert totals.total == Decimal("12.99")


def test_standard_rate_is_still_twenty_percent():
    totals = uk({"sku": "S-1", "description": "Kettle", "quantity": 1, "unit_price": "10.00", "category": "standard"})
    assert totals.tax == Decimal("2.00")
