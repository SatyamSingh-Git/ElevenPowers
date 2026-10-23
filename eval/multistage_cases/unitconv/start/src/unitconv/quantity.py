"""Quantities: a number with a unit, and reading them from text such as `12.5 km/h`."""
from dataclasses import dataclass
import re

from .compound import CompoundUnit, parse_unit
from .errors import ParseError

QUANTITY = re.compile(r'\s*(?P<number>[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*'
                      r'(?P<unit>[A-Za-z_][A-Za-z0-9_*/^-]*|1/[A-Za-z0-9_*/^-]+)\s*')


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: CompoundUnit


def parse_quantity(text):
    match = QUANTITY.fullmatch(text)
    if not match:
        raise ParseError(f"cannot parse quantity: '{text}'")
    # Unit lookup ignores case, so input is normalised before it is resolved.
    return Quantity(float(match.group('number')), parse_unit(match.group('unit').lower()))
