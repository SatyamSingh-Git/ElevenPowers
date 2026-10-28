from datetime import datetime

import pytest

from parcelpost.config import Settings
from parcelpost.core.address import make_address
from parcelpost.core.clock import FixedClock
from parcelpost.core.parcel import Parcel
from parcelpost.services.booking import Order


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path)


@pytest.fixture
def clock():
    # A Monday morning, before the collection cutoff.
    return FixedClock(datetime(2026, 3, 2, 10, 0))


@pytest.fixture
def make_order():
    def make(account="ACME", postcode="SW1A 1AA", weight_grams=2500, size=(20, 15, 10),
             declared_pence=0, **options):
        return Order(account, make_address("Ann Example", "1 High Street", "London", postcode),
                     Parcel(weight_grams, *size, declared_pence=declared_pence), **options)
    return make
