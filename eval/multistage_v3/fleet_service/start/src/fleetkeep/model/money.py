"""Money is held as whole cents; these helpers read, multiply and print it."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from ..errors import FleetError

CENT = Decimal("0.01")


def parse_money(text):
    """Cents from text such as `12.5`, `1,204.50` or `$88.10`."""
    cleaned = text.strip().replace(",", "").removeprefix("$")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise FleetError("E141", text=text) from None
    if not value.is_finite() or value < 0 or value != value.quantize(CENT, rounding=ROUND_HALF_UP):
        raise FleetError("E141", text=text)
    return int(value * 100)


def times(cents, quantity):
    """`cents` multiplied by a whole or decimal quantity, rounded half up to the cent."""
    return int((Decimal(cents) * Decimal(quantity)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def divide(cents, count):
    """`cents` split `count` ways, rounded half up to the cent."""
    return int((Decimal(cents) / count).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def dollars(cents):
    return (Decimal(cents) / 100).quantize(CENT)


def format_money(cents):
    return str(dollars(cents))
