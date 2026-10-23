"""Amounts: integer minor units inside, decimal text at the edges."""
import re

from ._generated import CURRENCIES
from .errors import AmountError

DEFAULT_CURRENCY = "USD"

_AMOUNT = re.compile(r"(-?)(\d+)(?:\.(\d+))?")


def currency_digits(currency):
    """Digits after the decimal point for `currency`, e.g. 2 for USD, 0 for JPY."""
    try:
        return CURRENCIES[currency][1]
    except KeyError:
        raise AmountError(f"unknown currency: {currency}") from None


def parse_amount(text, currency=DEFAULT_CURRENCY):
    """Read decimal text such as "-12.5" as integer minor units (-1250 for USD)."""
    digits = currency_digits(currency)
    match = _AMOUNT.fullmatch(text.strip())
    if not match:
        raise AmountError(f"invalid amount: {text}")
    sign, whole, fraction = match.group(1), match.group(2), match.group(3) or ""
    if len(fraction) > digits:
        raise AmountError(f"too many decimal places for {currency}: {text}")
    minor = int(whole) * 10**digits + int(fraction.ljust(digits, "0") or "0")
    return -minor if sign else minor


def format_amount(minor, currency=DEFAULT_CURRENCY):
    """Write integer minor units as decimal text: 1250 -> "12.50" in USD."""
    digits = currency_digits(currency)
    sign = "-" if minor < 0 else ""
    whole, fraction = divmod(abs(minor), 10**digits)
    if not digits:
        return f"{sign}{whole}"
    return f"{sign}{whole}.{fraction:0{digits}d}"
