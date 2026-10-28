"""Exact arithmetic for grades.

Scores are kept as fractions until the last step, so that a percent of
exactly 89.45 rounds to 89.5 instead of whatever its float happens to be.
"""
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction


def exact(number):
    """A number from a file or the command line, as the decimal it was written as."""
    if isinstance(number, Fraction):
        return number
    return Fraction(str(number))


def round_half_up(value, decimals):
    value = exact(value)
    quotient = Decimal(value.numerator) / Decimal(value.denominator)
    return float(quotient.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP))
