"""Units of measure and conversion between them.

Every unit belongs to one dimension. Mass and volume units convert through a
base unit (g and ml). Count units (a plain count, cloves, cans, slices) only
ever combine with themselves.
"""
from dataclasses import dataclass
from fractions import Fraction

from ..errors import UnitError

MASS = "mass"
VOLUME = "volume"
COUNT = "count"

BASE = {MASS: "g", VOLUME: "ml"}
METRIC = frozenset({"g", "kg", "ml", "l"})


@dataclass(frozen=True)
class Unit:
    symbol: str
    dimension: str
    # How many base units one of this unit holds; 1 for count units.
    factor: Fraction

    @property
    def metric(self):
        return self.symbol in METRIC


def _define(symbol, dimension, factor):
    return symbol, Unit(symbol, dimension, Fraction(factor))


UNITS = dict([
    _define("g", MASS, "1"),
    _define("kg", MASS, "1000"),
    _define("oz", MASS, "28.3495"),
    _define("lb", MASS, "453.592"),
    _define("ml", VOLUME, "1"),
    _define("l", VOLUME, "1000"),
    _define("tsp", VOLUME, "4.92892"),
    _define("tbsp", VOLUME, "14.7868"),
    _define("cup", VOLUME, "236.588"),
    _define("", COUNT, "1"),
    _define("clove", COUNT, "1"),
    _define("can", COUNT, "1"),
    _define("slice", COUNT, "1"),
])

ALIASES = {
    "gram": "g",
    "grams": "g",
    "gr": "g",
    "kilo": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "ounce": "oz",
    "ounces": "oz",
    "pound": "lb",
    "pounds": "lb",
    "lbs": "lb",
    "millilitre": "ml",
    "millilitres": "ml",
    "milliliter": "ml",
    "milliliters": "ml",
    "litre": "l",
    "litres": "l",
    "liter": "l",
    "liters": "l",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tbs": "tbsp",
    "cups": "cup",
    "cloves": "clove",
    "cans": "can",
    "tin": "can",
    "tins": "can",
    "slices": "slice",
}


def lookup(text):
    """The unit `text` names, or None when it names none. The empty string is a plain count."""
    key = text.strip().lower().rstrip(".")
    return UNITS.get(ALIASES.get(key, key))


def unit(text):
    found = lookup(text)
    if found is None:
        raise UnitError(f"unknown unit {text}")
    return found


def convertible(source, target):
    a, b = unit(source), unit(target)
    if a.dimension != b.dimension:
        return False
    return a.dimension != COUNT or a.symbol == b.symbol


def convert(amount, source, target):
    """`amount` of `source` expressed in `target`, exactly."""
    if not convertible(source, target):
        raise UnitError(f"cannot convert {source or 'each'} to {target or 'each'}")
    return amount * unit(source).factor / unit(target).factor


def to_base(amount, symbol):
    """`amount` of `symbol` in its dimension's base unit; count units are returned as they are."""
    found = unit(symbol)
    if found.dimension == COUNT:
        return amount, found.symbol
    return amount * found.factor, BASE[found.dimension]
