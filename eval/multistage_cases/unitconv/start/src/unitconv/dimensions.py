"""Physical dimensions as products of powers of six base dimensions."""
from dataclasses import dataclass

from .errors import UnitError

# length, mass, time, temperature, amount of substance, electric current
BASES = ('L', 'M', 'T', 'K', 'N', 'I')

NAMED = {
    'dimensionless': {},
    'length': {'L': 1},
    'area': {'L': 2},
    'volume': {'L': 3},
    'mass': {'M': 1},
    'time': {'T': 1},
    'temperature': {'K': 1},
    'amount': {'N': 1},
    'current': {'I': 1},
    'frequency': {'T': -1},
    'speed': {'L': 1, 'T': -1},
    'acceleration': {'L': 1, 'T': -2},
    'force': {'M': 1, 'L': 1, 'T': -2},
    'energy': {'M': 1, 'L': 2, 'T': -2},
    'power': {'M': 1, 'L': 2, 'T': -3},
    'pressure': {'M': 1, 'L': -1, 'T': -2},
}


def _power(base, exponent):
    return base if exponent == 1 else f'{base}^{exponent}'


@dataclass(frozen=True)
class Dimension:
    exponents: tuple = ()

    @classmethod
    def of(cls, powers):
        kept = [(base, power) for base, power in powers.items() if power]
        return cls(tuple(sorted(kept, key=lambda item: BASES.index(item[0]))))

    @classmethod
    def named(cls, name):
        if name not in NAMED:
            raise UnitError(f"unknown dimension: '{name}'")
        return cls.of(NAMED[name])

    def __mul__(self, other):
        powers = dict(self.exponents)
        for base, power in other.exponents:
            powers[base] = powers.get(base, 0) + power
        return Dimension.of(powers)

    def __pow__(self, exponent):
        return Dimension.of({base: power * exponent for base, power in self.exponents})

    def __truediv__(self, other):
        return self * other ** -1

    @property
    def formula(self):
        above = [_power(base, power) for base, power in self.exponents if power > 0]
        below = [_power(base, -power) for base, power in self.exponents if power < 0]
        return ('*'.join(above) or '1') + ''.join('/' + term for term in below)

    @property
    def name(self):
        return _NAMES.get(self, self.formula)


_NAMES = {Dimension.of(powers): name for name, powers in NAMED.items()}
