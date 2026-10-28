"""Declared values up to 5000.00 are accepted."""
from datetime import datetime

import pytest

from parcelpost.config import load_settings
from parcelpost.core.address import make_address
from parcelpost.core.clock import FixedClock
from parcelpost.core.errors import ValidationError
from parcelpost.core.parcel import Parcel
from parcelpost.services.booking import Order, book, quote_parcel


def test_four_thousand_pounds_can_be_declared(tmp_path):
    settings = load_settings(tmp_path)
    parcel = Parcel(1000, 20, 15, 10, declared_pence=400_000)
    assert quote_parcel(settings, parcel, "B1 1AA", "ground").amount("insurance") == 6000
    shipment = book(settings, Order("ACME", make_address("Pat", "1 Any Street", "Birmingham", "B1 1AA"), parcel),
                    clock=FixedClock(datetime(2026, 3, 2, 9, 0)))
    assert shipment.parcel.declared_pence == 400_000


def test_the_limit_is_five_thousand(tmp_path):
    settings = load_settings(tmp_path)
    quote_parcel(settings, Parcel(1000, 20, 15, 10, declared_pence=500_000), "B1 1AA", "ground")
    with pytest.raises(ValidationError) as raised:
        quote_parcel(settings, Parcel(1000, 20, 15, 10, declared_pence=500_001), "B1 1AA", "ground")
    assert str(raised.value) == "declared value 5000.01 is over the limit of 5000.00"
