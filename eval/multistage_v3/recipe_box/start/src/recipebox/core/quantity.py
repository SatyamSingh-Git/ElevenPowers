"""Amounts and quantities: reading them, writing them exactly, and showing them.

Amounts are kept as exact Fractions. Files store them exactly (`format_amount`);
what a person reads is rounded to something a cook would measure
(`display_amount`).
"""
from dataclasses import dataclass
from fractions import Fraction
import re

from ..errors import AmountError
from . import units

# Fractions a cook is shown for non-metric units.
DENOMINATORS = (2, 4, 8)
# Shown instead of zero, so a small amount never disappears.
SMALLEST = Fraction(1, 8)

VULGAR = {
    "½": Fraction(1, 2),
    "⅓": Fraction(1, 3),
    "⅔": Fraction(2, 3),
    "¼": Fraction(1, 4),
    "¾": Fraction(3, 4),
    "⅛": Fraction(1, 8),
    "⅜": Fraction(3, 8),
    "⅝": Fraction(5, 8),
    "⅞": Fraction(7, 8),
}

_WHOLE_OR_DECIMAL = re.compile(r"\d+(\.\d+)?|\.\d+")
_SLASHED = re.compile(r"(\d+)/(\d+)")


@dataclass(frozen=True)
class Quantity:
    amount: Fraction
    unit: str = ""

    @property
    def dimension(self):
        return units.unit(self.unit).dimension

    def to(self, symbol):
        return Quantity(units.convert(self.amount, self.unit, symbol), units.unit(symbol).symbol)

    def __str__(self):
        return display_quantity(self)


def _read_part(part):
    if _WHOLE_OR_DECIMAL.fullmatch(part):
        return Fraction(part)
    slashed = _SLASHED.fullmatch(part)
    if slashed and int(slashed.group(2)) != 0:
        return Fraction(int(slashed.group(1)), int(slashed.group(2)))
    if part[-1] in VULGAR:
        whole = part[:-1]
        if whole == "":
            return VULGAR[part]
        if whole.isdigit():
            return int(whole) + VULGAR[part[-1]]
    return None


def is_amount(token):
    """Whether `token` reads as one part of an amount, such as `2`, `3/4` or `1½`."""
    return _read_part(token) is not None


def parse_amount(text):
    """Read `2`, `0.75`, `3/4`, `1 1/2` or `1½` as an exact, positive Fraction."""
    parts = text.split()
    if not 1 <= len(parts) <= 2:
        raise AmountError(f"cannot read amount {text.strip()}")
    total = Fraction(0)
    for part in parts:
        value = _read_part(part)
        if value is None:
            raise AmountError(f"cannot read amount {text.strip()}")
        total += value
    if total <= 0:
        raise AmountError(f"cannot read amount {text.strip()}")
    return total


def parse_quantity(text):
    """Read `500 g`, `1 1/2 cup` or a bare count such as `3`."""
    tokens = text.split()
    amount_tokens = []
    while tokens and is_amount(tokens[0]) and len(amount_tokens) < 2:
        amount_tokens.append(tokens.pop(0))
    if not amount_tokens:
        raise AmountError(f"cannot read amount {text.strip()}")
    return Quantity(parse_amount(" ".join(amount_tokens)), units.unit(" ".join(tokens)).symbol)


def format_amount(amount):
    """Exact text for an amount: `2`, `3/4` or `1 1/2`."""
    amount = Fraction(amount)
    whole, rest = divmod(amount.numerator, amount.denominator)
    if rest == 0:
        return str(whole)
    fraction = f"{rest}/{amount.denominator}"
    return f"{whole} {fraction}" if whole else fraction


def _nearest(amount):
    whole = amount.numerator // amount.denominator
    rest = amount - whole
    best = Fraction(0)
    for denominator in DENOMINATORS:
        candidate = Fraction(round(rest * denominator), denominator)
        if abs(candidate - rest) < abs(best - rest):
            best = candidate
    return max(whole + best, SMALLEST)


def _decimal(amount, places):
    text = f"{float(amount):.{places}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def display_amount(amount, symbol=""):
    """What a person is shown: whole g and ml, kg and l to two places, cook's fractions otherwise."""
    if symbol in ("g", "ml"):
        return str(max(round(amount), 1))
    if symbol in units.METRIC:
        return _decimal(amount, 2)
    return format_amount(_nearest(Fraction(amount)))


def display_quantity(quantity):
    text = display_amount(quantity.amount, quantity.unit)
    return f"{text} {quantity.unit}" if quantity.unit else text
