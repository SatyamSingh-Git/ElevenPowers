from decimal import (ROUND_CEILING, ROUND_DOWN, ROUND_FLOOR, ROUND_HALF_DOWN, ROUND_HALF_EVEN,
                     ROUND_HALF_UP, ROUND_UP, Context, Decimal)

from .errors import UnitError

MODES = {
    'half_even': ROUND_HALF_EVEN,
    'half_up': ROUND_HALF_UP,
    'half_down': ROUND_HALF_DOWN,
    'up': ROUND_UP,
    'down': ROUND_DOWN,
    'ceiling': ROUND_CEILING,
    'floor': ROUND_FLOOR,
}

# Wide enough that quantizing a large value to 15 places never runs out of digits.
_CONTEXT = Context(prec=60)


def round_value(value, precision, mode):
    if mode not in MODES:
        raise UnitError(f"unknown rounding mode: '{mode}'")
    # str() rather than the float itself, so 2.675 rounds as the 2.675 the user typed.
    exact = Decimal(str(value))
    return float(exact.quantize(Decimal(1).scaleb(-precision), rounding=MODES[mode], context=_CONTEXT))
