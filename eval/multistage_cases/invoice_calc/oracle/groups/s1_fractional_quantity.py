from decimal import Decimal

import pytest

from invoicekit import compute, invoice_from_dict


def invoice(*lines):
    return invoice_from_dict({"number": "H-1", "issued": "2026-05-04", "region": "US-NY", "currency": "USD",
                              "lines": list(lines)})


def line(quantity, price="10.00", category="standard", sku="X-1"):
    return {"sku": sku, "description": "Work", "quantity": quantity, "unit_price": price, "category": category}


def test_fractional_quantities_are_charged():
    totals = compute(invoice(line("1.5", "80.00", "services", "SV-2"), line("0.25", "100.00", "standard", "C-1")))
    assert [item.gross for item in totals.lines] == [Decimal("120.00"), Decimal("25.00")]
    assert totals.subtotal == Decimal("145.00")
    assert totals.tax == Decimal("2.22")
    assert totals.total == Decimal("147.22")


def test_line_amount_is_rounded_to_the_cent():
    assert compute(invoice(line("2.5", "19.99"))).subtotal == Decimal("49.98")


@pytest.mark.parametrize("quantity, subtotal", [
    ("0.01", "0.10"), ("10000", "100000.00"), (4, "40.00"), ("2.50", "25.00"), ("7", "70.00"),
])
def test_quantities_in_range_are_accepted(quantity, subtotal):
    assert compute(invoice(line(quantity))).subtotal == Decimal(subtotal)


@pytest.mark.parametrize("quantity", ["0.125", "1.333", "2.005"])
def test_more_than_two_places_is_refused(quantity):
    with pytest.raises(ValueError, match="quantity has more than 2 decimal places"):
        invoice(line(quantity))


@pytest.mark.parametrize("quantity", ["0", 0, "10000.01", "20000"])
def test_out_of_range_names_the_new_minimum(quantity):
    with pytest.raises(ValueError, match="quantity must be between 0.01 and 10000"):
        invoice(line(quantity))
