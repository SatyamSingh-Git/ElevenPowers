"""The unit registry: every spelling a unit can be written in, resolved to a Unit."""
from dataclasses import dataclass

from . import _generated
from .dimensions import Dimension
from .errors import UnknownUnitError


@dataclass(frozen=True)
class Unit:
    symbol: str
    name: str
    plural: str
    dimension: Dimension
    factor: float
    offset: float = 0
    prefixable: bool = False


def _number(text):
    if '/' in text:
        numerator, denominator = text.split('/')
        return float(numerator) / float(denominator)
    return float(text)


class Registry:
    def __init__(self, units=_generated.UNITS, prefixes=_generated.PREFIXES):
        self._units = []
        self._spellings = {}
        for symbol, name, plural, dimension, factor, offset, prefixable in units:
            unit = Unit(symbol, name, plural, Dimension.named(dimension), _number(factor), _number(offset), prefixable)
            self._units.append(unit)
            self._spellings[symbol] = unit
        for prefix, prefix_name, prefix_factor in prefixes:
            for unit in self._units:
                if unit.prefixable:
                    self._spellings.setdefault(prefix + unit.symbol, Unit(
                        prefix + unit.symbol, prefix_name + unit.name, prefix_name + unit.plural,
                        unit.dimension, _number(prefix_factor) * unit.factor))
        # On a clash between spellings that differ only in case, the one registered first wins.
        self._folded = {}
        for spelling, unit in self._spellings.items():
            self._folded.setdefault(spelling.lower(), unit)

    def lookup(self, symbol):
        unit = self._spellings.get(symbol) or self._folded.get(symbol.lower())
        if unit is None:
            raise UnknownUnitError(symbol)
        return unit

    def units(self, dimension=None):
        return [unit for unit in self._units if dimension is None or unit.dimension == dimension]


REGISTRY = Registry()
