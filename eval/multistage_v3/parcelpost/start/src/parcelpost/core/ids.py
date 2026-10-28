"""Tracking numbers: PP, an eight-digit serial, one check digit, GB."""
from itertools import cycle

PREFIX = "PP"
COUNTRY = "GB"
SERIAL_DIGITS = 8


def new_tracking_number(sequence):
    if not 0 < sequence < 10 ** SERIAL_DIGITS:
        raise ValueError(f"sequence out of range: {sequence}")
    serial = f"{sequence:0{SERIAL_DIGITS}d}"
    return f"{PREFIX}{serial}{_check_digit(serial)}{COUNTRY}"


def _check_digit(serial):
    total = sum(int(digit) * weight for digit, weight in zip(serial, cycle((3, 1))))
    return (10 - total % 10) % 10
