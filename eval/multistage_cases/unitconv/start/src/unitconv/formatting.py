"""Turning quantities into text, and into records for JSON output and batch files."""
from decimal import Decimal

from .errors import UnitError
from .settings import STYLES


def format_number(value):
    """Plain decimal notation, never an exponent, without trailing zeros."""
    text = format(Decimal(str(value)), 'f')
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    return '0' if text == '-0' else text


def format_quantity(quantity, *, style='symbol'):
    if style not in STYLES:
        raise UnitError(f"unknown style: '{style}'")
    number = format_number(quantity.value)
    if style == 'name':
        return f'{number} {quantity.unit.name(plural=number != "1")}'
    return f'{number} {quantity.unit.symbol}'


def result_record(text, result, *, style='symbol'):
    return {
        'input': text,
        'value': result.value,
        'unit': result.unit.symbol,
        'text': format_quantity(result, style=style),
    }
