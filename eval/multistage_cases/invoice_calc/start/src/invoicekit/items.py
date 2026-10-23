from dataclasses import dataclass
from decimal import Decimal

from .money import MoneyError, to_decimal

CATEGORIES = ("standard", "food", "books", "digital", "services")
REQUIRED_FIELDS = ("sku", "description", "quantity", "unit_price")
MIN_QUANTITY = 1
MAX_QUANTITY = 10_000
MAX_DESCRIPTION = 120


class ItemError(ValueError):
    pass


@dataclass(frozen=True)
class LineItem:
    sku: str
    description: str
    quantity: int
    unit_price: Decimal
    category: str = "standard"

    @property
    def gross(self):
        return self.quantity * self.unit_price


def parse_quantity(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ItemError("quantity must be a whole number")
    if not MIN_QUANTITY <= value <= MAX_QUANTITY:
        raise ItemError(f"quantity must be between {MIN_QUANTITY} and {MAX_QUANTITY}")
    return value


def parse_unit_price(value):
    try:
        price = to_decimal(value)
    except MoneyError as error:
        raise ItemError(f"unit price: {error}") from None
    if price < 0:
        raise ItemError("unit price must not be negative")
    return price


def line_from_dict(data):
    for name in REQUIRED_FIELDS:
        if name not in data:
            raise ItemError(f"line item missing field: {name}")
    sku = str(data["sku"]).strip()
    if not sku:
        raise ItemError("sku must not be empty")
    description = str(data["description"]).strip()
    if len(description) > MAX_DESCRIPTION:
        raise ItemError(f"description must be at most {MAX_DESCRIPTION} characters")
    category = data.get("category", "standard")
    if category not in CATEGORIES:
        raise ItemError(f"unknown category: {category}")
    return LineItem(
        sku=sku,
        description=description,
        quantity=parse_quantity(data["quantity"]),
        unit_price=parse_unit_price(data["unit_price"]),
        category=category,
    )
