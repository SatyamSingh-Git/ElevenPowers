from .compound import parse_unit
from .errors import IncompatibleUnitsError
from .quantity import Quantity
from .rounding import round_value
from .settings import DEFAULT_PRECISION, DEFAULT_ROUNDING, check_precision


def convert(quantity, target, *, precision=DEFAULT_PRECISION, rounding=DEFAULT_ROUNDING):
    """Convert `quantity` to `target` (a unit expression or CompoundUnit), rounded to `precision` places."""
    if isinstance(target, str):
        target = parse_unit(target)
    source = quantity.unit
    if source.dimension != target.dimension:
        raise IncompatibleUnitsError(
            f'cannot convert {source.symbol} ({source.dimension.name}) to {target.symbol} ({target.dimension.name})')
    check_precision(precision)
    base = (quantity.value + source.offset) * source.factor
    value = base / target.factor - target.offset
    return Quantity(round_value(value, precision, rounding), target)
