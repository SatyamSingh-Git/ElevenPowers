"""Amounts are integer cents everywhere inside the program.

Text only becomes cents at the edges: the command line, statements and the
files in a workspace.
"""
import math

from ..errors import ValidationError


def parse_amount(text):
    """Read amount text such as ``-12.50``, ``1,204.00`` or ``(3.20)`` as cents."""
    cleaned = text.strip().replace(",", "")
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    if negative:
        cleaned = cleaned[1:-1].strip()
    try:
        value = float(cleaned)
    except ValueError:
        raise ValidationError(f"invalid amount: {text}") from None
    if not math.isfinite(value):
        raise ValidationError(f"invalid amount: {text}")
    cents = int(value * 100)
    return -cents if negative else cents


def format_amount(cents):
    """``-1,234.56``: amounts in reports people read."""
    sign = "-" if cents < 0 else ""
    whole, part = divmod(abs(cents), 100)
    return f"{sign}{whole:,}.{part:02d}"


def decimal_text(cents):
    """``-1234.56``: amounts in files and CSV that other programs read."""
    sign = "-" if cents < 0 else ""
    whole, part = divmod(abs(cents), 100)
    return f"{sign}{whole}.{part:02d}"


def share(part, whole):
    """`part` as a whole-number percentage of `whole`, or None when `whole` is zero."""
    if whole == 0:
        return None
    return round(part * 100 / whole)
