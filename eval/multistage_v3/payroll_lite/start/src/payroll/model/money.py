"""Money is a Decimal rounded half-up to the cent; these helpers keep that rule in one place."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from payroll.errors import PayrollError

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def round_money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def parse_money(text, what="amount"):
    """An amount typed by a person or read from a file: `12`, `12.5` or `1,250.00`."""
    cleaned = str(text).strip().replace(",", "")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise PayrollError(f"{what} is not an amount: {text}") from None
    if not value.is_finite():
        raise PayrollError(f"{what} is not an amount: {text}")
    return round_money(value)


def parse_rate(text, what="rate"):
    """A percentage such as `5` or `2.5`, kept exactly as written."""
    try:
        value = Decimal(str(text).strip())
    except InvalidOperation:
        raise PayrollError(f"{what} is not a number: {text}") from None
    if not value.is_finite():
        raise PayrollError(f"{what} is not a number: {text}")
    if value < 0:
        raise PayrollError(f"{what} must not be negative: {text}")
    return value


def percent_of(amount, rate):
    return round_money(amount * rate / 100)


def total(amounts):
    return sum(amounts, ZERO)


def format_money(value):
    """For people: thousands separators and two decimals."""
    return f"{round_money(value):,.2f}"


def plain_money(value):
    """For files: two decimals and nothing else."""
    return f"{round_money(value):.2f}"
