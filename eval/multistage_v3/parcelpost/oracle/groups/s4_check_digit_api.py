"""Issued tracking numbers carry the S10 check digit."""
from datetime import datetime
import re

from parcelpost.config import load_settings
from parcelpost.core.address import make_address
from parcelpost.core.clock import FixedClock
from parcelpost.core.parcel import Parcel
from parcelpost.services.booking import Order, book

WEIGHTS = (8, 6, 4, 2, 3, 5, 9, 7)


def s10_check(serial):
    check = 11 - sum(int(digit) * weight for digit, weight in zip(serial, WEIGHTS)) % 11
    return {10: 0, 11: 5}.get(check, check)


def test_booked_numbers_have_s10_check_digits(tmp_path):
    settings = load_settings(tmp_path)
    clock = FixedClock(datetime(2026, 3, 2, 9, 0))
    order = Order("ACME", make_address("Pat", "1 Any Street", "London", "SW1A 1AA"), Parcel(1000, 20, 15, 10))
    numbers = [book(settings, order, clock=clock).tracking_number for _ in range(6)]
    assert len(set(numbers)) == 6
    for number in numbers:
        match = re.fullmatch(r"PP(\d{8})(\d)GB", number)
        assert match, number
        assert int(match.group(2)) == s10_check(match.group(1)), number
