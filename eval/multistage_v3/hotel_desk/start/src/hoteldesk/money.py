"""Money is held as integer cents; these helpers convert at the edges."""
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_UP

from .errors import ValidationError

CENT = Decimal("0.01")


def parse_money(text):
    """'12.5' -> 1250. Refuses negative amounts and fractions of a cent."""
    try:
        value = Decimal(str(text).strip())
    except InvalidOperation:
        raise ValidationError(f"Not an amount: {text}") from None
    if not value.is_finite() or value < 0:
        raise ValidationError(f"Not an amount: {text}")
    if value != value.quantize(CENT):
        raise ValidationError(f"Amount has more than two decimals: {text}")
    return int(value * 100)


def format_money(cents):
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def adjust(cents, percent):
    """Raise an amount by `percent` (lower it, if negative), to the nearest cent."""
    value = Decimal(cents) * (100 + Decimal(percent)) / 100
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def per(cents, count):
    """An amount shared over `count`, to the nearest cent; nothing when there is nothing to share."""
    if not count:
        return 0
    return int((Decimal(cents) / count).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def tax_on(cents, rate):
    return int((Decimal(cents) * rate).quantize(Decimal(1), rounding=ROUND_DOWN))
