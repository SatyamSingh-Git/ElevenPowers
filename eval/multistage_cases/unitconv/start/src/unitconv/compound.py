"""Compound unit expressions such as kg*m/s^2."""
from dataclasses import dataclass
import re

from .dimensions import Dimension
from .errors import ParseError, UnitError
from .registry import REGISTRY

TERM = re.compile(r'([A-Za-z_]+)(?:\^(-?\d+))?')
SPOKEN_POWERS = {2: 'squared', 3: 'cubed'}


def _power(symbol, exponent):
    return symbol if exponent == 1 else f'{symbol}^{exponent}'


def _spoken(name, exponent):
    if exponent == 1:
        return name
    return f'{name} {SPOKEN_POWERS.get(exponent, f"to the power {exponent}")}'


@dataclass(frozen=True)
class CompoundUnit:
    terms: tuple  # ((Unit, exponent), ...) in the order written; no exponent is zero

    @property
    def dimension(self):
        dimension = Dimension()
        for unit, exponent in self.terms:
            dimension = dimension * unit.dimension ** exponent
        return dimension

    @property
    def factor(self):
        factor = 1
        for unit, exponent in self.terms:
            factor *= unit.factor ** exponent
        return factor

    @property
    def offset(self):
        return self.terms[0][0].offset if len(self.terms) == 1 else 0

    @property
    def symbol(self):
        above = [_power(unit.symbol, exponent) for unit, exponent in self.terms if exponent > 0]
        below = [_power(unit.symbol, -exponent) for unit, exponent in self.terms if exponent < 0]
        return ('*'.join(above) or '1') + ''.join('/' + term for term in below)

    def name(self, plural=False):
        above = [(unit, exponent) for unit, exponent in self.terms if exponent > 0]
        below = [(unit, -exponent) for unit, exponent in self.terms if exponent < 0]
        words = [_spoken(unit.plural if plural and i == len(above) - 1 else unit.name, exponent)
                 for i, (unit, exponent) in enumerate(above)]
        words += ['per ' + _spoken(unit.name, exponent) for unit, exponent in below]
        return ' '.join(words)


def parse_unit(text):
    """Parse `kg*m/s^2`; each `/` divides by the one term that follows it."""
    pieces = re.split(r'([*/])', text.replace(' ', ''))
    if len(pieces) > 1 and pieces[:2] == ['1', '/']:
        pieces = pieces[2:]
        sign = -1
    else:
        sign = 1
    powers = {}
    for i, piece in enumerate(pieces):
        if i % 2:
            sign = 1 if piece == '*' else -1
            continue
        match = TERM.fullmatch(piece)
        if not match:
            raise ParseError(f"cannot parse unit: '{text}'")
        unit = REGISTRY.lookup(match.group(1))
        powers[unit] = powers.get(unit, 0) + sign * int(match.group(2) or 1)
    terms = tuple((unit, exponent) for unit, exponent in powers.items() if exponent)
    if not terms:
        raise ParseError(f"cannot parse unit: '{text}'")
    for unit, exponent in terms:
        if unit.offset and (len(terms) > 1 or exponent != 1):
            raise UnitError(f"offset unit '{unit.symbol}' cannot be combined")
    return CompoundUnit(terms)
