from decimal import Decimal

import pytest

from invoicekit.items import ItemError, line_from_dict

WIDGET = {"sku": "W-100", "description": "Widget", "quantity": 3, "unit_price": "19.99"}


def test_line_from_dict_reads_a_line():
    item = line_from_dict(WIDGET)
    assert item.quantity == 3
    assert item.unit_price == Decimal("19.99")
    assert item.category == "standard"
    assert item.gross == Decimal("59.97")


@pytest.mark.parametrize("field", ["sku", "description", "quantity", "unit_price"])
def test_missing_field(field):
    data = {key: value for key, value in WIDGET.items() if key != field}
    with pytest.raises(ItemError, match=f"line item missing field: {field}"):
        line_from_dict(data)


@pytest.mark.parametrize("quantity", ["3", 1.5, True])
def test_quantity_must_be_a_whole_number(quantity):
    with pytest.raises(ItemError, match="quantity must be a whole number"):
        line_from_dict({**WIDGET, "quantity": quantity})


@pytest.mark.parametrize("quantity", [0, 10_001])
def test_quantity_range(quantity):
    with pytest.raises(ItemError, match="quantity must be between 1 and 10000"):
        line_from_dict({**WIDGET, "quantity": quantity})


def test_unknown_category():
    with pytest.raises(ItemError, match="unknown category: toys"):
        line_from_dict({**WIDGET, "category": "toys"})


def test_negative_unit_price():
    with pytest.raises(ItemError, match="unit price must not be negative"):
        line_from_dict({**WIDGET, "unit_price": "-1"})
