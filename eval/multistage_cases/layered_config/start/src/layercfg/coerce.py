"""Turning raw strings from any layer into typed values, and checking ranges."""
from decimal import Decimal
import math
import re

from ._generated import BOOLEAN_WORDS, DURATION_UNITS, SIZE_UNITS
from .errors import CoercionError

_DURATION = re.compile(r'^(\d+(?:\.\d+)?)\s*([a-z]*)$')
_SIZE = re.compile(r'^(\d+)\s*([a-z]*)$')


def _expected(type_name, text):
    return CoercionError(f"expected {type_name}, got '{text}'")


def _int(option, text):
    try:
        return int(text)
    except ValueError:
        raise _expected('int', text) from None


def _float(option, text):
    try:
        value = float(text)
    except ValueError:
        raise _expected('float', text) from None
    if not math.isfinite(value):
        raise _expected('float', text)
    return value


def _bool(option, text):
    if text not in BOOLEAN_WORDS:
        raise _expected('bool', text)
    return BOOLEAN_WORDS[text]


def _str(option, text):
    return text


def _duration(option, text):
    match = _DURATION.match(text.lower())
    if not match or (match.group(2) or 's') not in DURATION_UNITS:
        raise _expected('duration', text)
    milliseconds = Decimal(match.group(1)) * DURATION_UNITS[match.group(2) or 's']
    return float(milliseconds / 1000)


def _size(option, text):
    match = _SIZE.match(text.lower())
    if not match or (match.group(2) or 'b') not in SIZE_UNITS:
        raise _expected('size', text)
    return int(match.group(1)) * SIZE_UNITS[match.group(2) or 'b']


def _list(option, text):
    return [item.strip() for item in text.split(',') if item.strip()]


def _choice(option, text):
    if text not in option.choices:
        raise CoercionError(f"must be one of {', '.join(option.choices)}")
    return text


_COERCERS = {
    'int': _int,
    'float': _float,
    'bool': _bool,
    'str': _str,
    'duration': _duration,
    'size': _size,
    'list': _list,
    'choice': _choice,
}


def coerce(option, raw):
    """The typed value of `raw` for `option`; CoercionError says why not."""
    return _COERCERS[option.type](option, raw.strip())


def check_range(option, value):
    """A message if `value` is outside the option's range, else None."""
    if option.minimum is not None and value < coerce(option, option.minimum):
        return f'must be at least {option.minimum}'
    if option.maximum is not None and value > coerce(option, option.maximum):
        return f'must be at most {option.maximum}'
    return None
