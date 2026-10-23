"""Validation and parsing shared by the library and the command line."""
from decimal import Decimal
import re

from ._generated import LOCATION_KINDS, UNITS

MAX_QTY = 1_000_000
MAX_NAME = 80
MOVEMENT_TYPES = ('receive', 'issue', 'transfer', 'adjust')

SKU_PATTERN = re.compile(r'[A-Z0-9][A-Z0-9-]{0,23}')
CODE_PATTERN = re.compile(r'[A-Z0-9][A-Z0-9-]{0,11}')
WHOLE_PATTERN = re.compile(r'[0-9]+')
MONEY_PATTERN = re.compile(r'[0-9]+(\.[0-9]{1,2})?')


class StockError(Exception):
    """A request the inventory refuses. The message is shown to the user as it is."""


def normalize_sku(text):
    sku = str(text).strip().upper()
    if not SKU_PATTERN.fullmatch(sku):
        raise StockError(f'invalid sku: {text}')
    return sku


def normalize_code(text):
    code = str(text).strip().upper()
    if not CODE_PATTERN.fullmatch(code):
        raise StockError(f'invalid location code: {text}')
    return code


def _whole(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    return int(text) if WHOLE_PATTERN.fullmatch(text) else None


def parse_qty(value):
    """A quantity moved by one movement: a whole number from 1 to MAX_QTY."""
    qty = _whole(value)
    if qty is None or not 1 <= qty <= MAX_QTY:
        raise StockError(f'quantity must be a whole number from 1 to {MAX_QTY}: {value}')
    return qty


def parse_count(value):
    """A counted quantity, which unlike a movement may be zero."""
    count = _whole(value)
    if count is None or not 0 <= count <= MAX_QTY:
        raise StockError(f'count must be a whole number from 0 to {MAX_QTY}: {value}')
    return count


def parse_reorder_point(value):
    point = _whole(value)
    if point is None or not 0 <= point <= MAX_QTY:
        raise StockError(f'reorder point must be a whole number from 0 to {MAX_QTY}: {value}')
    return point


def parse_money(value):
    """Dollars and cents such as '2.50', '3' or '$0.12', as a Decimal with two places."""
    text = str(value).strip().removeprefix('$')
    if not MONEY_PATTERN.fullmatch(text):
        raise StockError(f'cost must be dollars and cents, like 2.50: {value}')
    return Decimal(text).quantize(Decimal('0.01'))


def format_money(amount):
    return f'${amount:,.2f}'


def check_name(name):
    name = str(name).strip()
    if not 1 <= len(name) <= MAX_NAME:
        raise StockError(f'item name must be 1 to {MAX_NAME} characters')
    return name


def check_unit(unit):
    if unit not in UNITS:
        raise StockError(f"unknown unit: {unit} (expected one of {', '.join(UNITS)})")
    return unit


def check_kind(kind):
    if kind not in LOCATION_KINDS:
        raise StockError(f"unknown location kind: {kind} (expected one of {', '.join(LOCATION_KINDS)})")
    return kind
