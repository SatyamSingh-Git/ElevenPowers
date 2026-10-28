"""Weights are integer grams and lengths whole centimetres."""
from decimal import Decimal, InvalidOperation

from .errors import ValidationError

GRAMS_PER_KG = 1000
GRAM = Decimal("0.001")


def kg_to_grams(text):
    try:
        value = Decimal(str(text).strip())
    except InvalidOperation:
        raise ValidationError(f"invalid weight: {text}") from None
    if not value.is_finite() or value <= 0 or value != value.quantize(GRAM):
        raise ValidationError(f"invalid weight: {text}")
    return int(value * GRAMS_PER_KG)


def format_kg(grams):
    whole, rest = divmod(grams, GRAMS_PER_KG)
    if not rest:
        return str(whole)
    return f"{whole}.{rest:03d}".rstrip("0")


def parse_size(text):
    parts = str(text).lower().split("x")
    if len(parts) != 3 or not all(part.strip().isdigit() for part in parts):
        raise ValidationError(f"invalid size: {text} (expected LxWxH in cm)")
    return tuple(int(part) for part in parts)


def round_up(value, step):
    return -(-value // step) * step
