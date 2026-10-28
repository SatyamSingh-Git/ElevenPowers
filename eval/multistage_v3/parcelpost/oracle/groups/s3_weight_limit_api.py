"""Exactly 30 kg is accepted for quoting and booking; heavier parcels get the new message."""
from datetime import datetime

import pytest

from parcelpost.config import load_settings
from parcelpost.core.address import make_address
from parcelpost.core.clock import FixedClock
from parcelpost.core.errors import ValidationError
from parcelpost.core.parcel import Parcel
from parcelpost.services.booking import Order, book, quote_parcel


def test_thirty_kilograms_is_accepted(tmp_path):
    settings = load_settings(tmp_path)
    parcel = Parcel(30_000, 40, 30, 30)
    assert quote_parcel(settings, parcel, "B1 1AA", "ground").total > 0
    shipment = book(settings, Order("ACME", make_address("Pat", "1 Any Street", "Birmingham", "B1 1AA"), parcel),
                    clock=FixedClock(datetime(2026, 3, 2, 9, 0)))
    assert shipment.parcel.weight_grams == 30_000


def test_heavier_parcels_are_refused_with_the_new_message(tmp_path):
    settings = load_settings(tmp_path)
    with pytest.raises(ValidationError) as raised:
        quote_parcel(settings, Parcel(30_500, 40, 30, 30), "B1 1AA", "ground")
    assert str(raised.value) == "parcel over the 30 kg limit: 30.5 kg"
