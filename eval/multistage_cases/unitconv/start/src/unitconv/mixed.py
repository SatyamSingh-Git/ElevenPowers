"""Mixed-unit results such as `5 ft 10.866142 in`: whole numbers of each unit but the last."""
import math

from .compound import parse_unit
from .convert import convert
from .errors import UnitError
from .formatting import format_quantity
from .quantity import Quantity
from .rounding import round_value
from .settings import DEFAULT_PRECISION, DEFAULT_ROUNDING, MAX_PRECISION


def split_quantity(quantity, targets, *, precision=DEFAULT_PRECISION, rounding=DEFAULT_ROUNDING):
    """Split `quantity` over the `targets` unit expressions, largest first; returns a list of Quantity."""
    units = [parse_unit(target) for target in targets]
    if len(units) < 2:
        raise UnitError('a mixed result needs at least two units')
    for unit in units:
        if unit.offset:
            raise UnitError(f"offset unit '{unit.symbol}' cannot be combined")
    if quantity.value < 0:
        raise UnitError('a mixed result needs a quantity of zero or more')
    remaining = quantity
    parts = []
    for unit in units[:-1]:
        exact = convert(remaining, unit, precision=MAX_PRECISION).value
        whole = math.floor(exact)
        parts.append(Quantity(whole, unit))
        remaining = Quantity(exact - whole, unit)
    last = convert(remaining, units[-1], precision=precision, rounding=rounding).value
    # Rounding can lift the remainder to a whole unit of the one before it: 5 ft 12 in is 6 ft 0 in.
    carry = convert(Quantity(1, units[-2]), units[-1], precision=precision, rounding=rounding).value
    if last >= carry:
        parts[-1] = Quantity(parts[-1].value + 1, units[-2])
        last = round_value(last - carry, precision, rounding)
    parts.append(Quantity(last, units[-1]))
    return parts


def format_mixed(parts, *, style='symbol'):
    return ' '.join(format_quantity(part, style=style) for part in parts)
