"""Currencies and money formatting, from the generated ISO 4217 table."""
from ._generated import CURRENCIES
from .errors import ReportError
from .numbers import format_number


def currency(code):
    """The ``(symbol, minor units)`` pair for an ISO 4217 code."""
    try:
        return CURRENCIES[code.upper()]
    except KeyError:
        raise ReportError(f"unknown currency: {code}") from None


def format_money(value, code="USD"):
    """``-$1,234.50``: the sign goes before the symbol, decimals follow the currency."""
    symbol, places = currency(code)
    text = format_number(value, places)
    if text.startswith("-"):
        return f"-{symbol}{text[1:]}"
    return f"{symbol}{text}"
