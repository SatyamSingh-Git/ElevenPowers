"""Sensor kinds, their canonical units and conversion into them.

The catalog in ``_generated.py`` says which unit each kind is stored in, which
units a controller may report it in, the range a working sensor can read and
how many decimals a value keeps.
"""
from .._generated import SENSOR_KINDS
from .errors import ValidationError

CONVERSIONS = {
    ("F", "C"): lambda value: (value - 32) * 5 / 9,
    ("C", "F"): lambda value: value * 9 / 5 + 32,
    ("klux", "lux"): lambda value: value * 1000,
    ("lux", "klux"): lambda value: value / 1000,
}


def kinds():
    return sorted(SENSOR_KINDS)


def check_kind(kind):
    kind = kind.strip()
    if kind not in SENSOR_KINDS:
        raise ValidationError(f"unknown kind: {kind}")
    return kind


def canonical_unit(kind):
    return SENSOR_KINDS[kind]["unit"]


def decimals(kind):
    return SENSOR_KINDS[kind]["decimals"]


def round_for(kind, value):
    return round(value, decimals(kind))


def format_value(kind, value):
    return f"{value:.{decimals(kind)}f}"


def convert(value, source, target):
    if source == target:
        return value
    try:
        conversion = CONVERSIONS[(source, target)]
    except KeyError:
        raise ValidationError(f"cannot convert {source} to {target}") from None
    return conversion(value)


def to_canonical(kind, value, unit):
    """Convert a value reported in ``unit`` to the kind's canonical unit."""
    unit = unit.strip()
    if unit not in SENSOR_KINDS[kind]["accepts"]:
        raise ValidationError(f"unknown unit {unit} for {kind}")
    return convert(value, unit, canonical_unit(kind))


def valid_range(kind):
    entry = SENSOR_KINDS[kind]
    return entry["min"], entry["max"]


def check_range(kind, value):
    """Return the value if a working sensor of this kind can read it."""
    low, high = valid_range(kind)
    if not low <= value <= high:
        raise ValidationError(f"out of range: {format_value(kind, value)} {canonical_unit(kind)}")
    return value
