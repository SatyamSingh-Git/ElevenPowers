"""Amounts are integer pence everywhere inside; they become decimals only at the edges."""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .errors import ValidationError

PENNY = Decimal("0.01")


def parse_amount(text):
    try:
        value = Decimal(str(text).strip())
    except InvalidOperation:
        raise ValidationError(f"invalid amount: {text}") from None
    if not value.is_finite() or value < 0 or value != value.quantize(PENNY):
        raise ValidationError(f"invalid amount: {text}")
    return int(value * 100)


def format_amount(pence):
    sign = "-" if pence < 0 else ""
    pounds, rest = divmod(abs(pence), 100)
    return f"{sign}{pounds}.{rest:02d}"


def percent_of(pence, percent):
    share = Decimal(pence) * Decimal(percent) / 100
    return int(share.quantize(Decimal(1), rounding=ROUND_HALF_UP))
