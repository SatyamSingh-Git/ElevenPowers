from decimal import Decimal

import pytest

from invoicekit.discounts import AmountOff, DiscountError, PercentOff, allocate, discount_from_dict
from invoicekit.items import line_from_dict


def lines(*specs):
    return [line_from_dict({"sku": f"S{n}", "description": "x", "quantity": 1, "unit_price": price,
                            "category": category}) for n, (price, category) in enumerate(specs)]


def test_percent_off_only_touches_its_category():
    items = lines(("10.00", "standard"), ("20.00", "books"))
    taken = allocate(items, [Decimal("10.00"), Decimal("20.00")], [PercentOff(Decimal(10), "books")], "USD", "half-up")
    assert taken == [Decimal(0), Decimal("2.00")]


def test_amount_off_adds_up_exactly():
    items = lines(("10.00", "standard"), ("10.00", "standard"), ("10.00", "standard"))
    taken = allocate(items, [Decimal("10.00")] * 3, [AmountOff(Decimal("10.00"))], "USD", "half-up")
    assert sum(taken) == Decimal("10.00")
    assert taken == [Decimal("3.34"), Decimal("3.33"), Decimal("3.33")]


def test_amount_off_is_capped_at_what_is_left():
    items = lines(("5.00", "standard"))
    taken = allocate(items, [Decimal("5.00")], [PercentOff(Decimal(20)), AmountOff(Decimal(50))], "USD", "half-up")
    assert taken == [Decimal("5.00")]


def test_discount_from_dict():
    assert discount_from_dict({"kind": "percent", "percent": "15"}) == PercentOff(Decimal(15))
    assert discount_from_dict({"kind": "amount", "amount": 5}) == AmountOff(Decimal(5))


@pytest.mark.parametrize("data, message", [
    ({"kind": "percent", "percent": "101"}, "discount percent must be between 0 and 100"),
    ({"kind": "amount", "amount": "-1"}, "discount amount must not be negative"),
    ({"kind": "coupon"}, "unknown discount kind: coupon"),
    ({"kind": "amount"}, "discount missing field: amount"),
])
def test_bad_discounts(data, message):
    with pytest.raises(DiscountError, match=message):
        discount_from_dict(data)
