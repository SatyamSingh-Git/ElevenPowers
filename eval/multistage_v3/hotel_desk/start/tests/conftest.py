from datetime import date, datetime

import pytest

from hoteldesk.clock import FixedClock
from hoteldesk.config import Settings
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)

SETUP = {
    "name": "Harbour View Inn",
    "room_types": [
        {"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"},
        {"code": "KG", "name": "King", "max_adults": 2, "base_rate": "150.00"},
        {"code": "ST", "name": "Suite", "max_adults": 4, "base_rate": "260.00"},
    ],
    "rooms": [
        {"number": "101", "type": "QN"},
        {"number": "102", "type": "QN"},
        {"number": "201", "type": "KG"},
        {"number": "202", "type": "KG"},
        {"number": "301", "type": "ST"},
    ],
    "rate_plans": [
        {"code": "BAR", "name": "Best available"},
        {"code": "AAA", "name": "Motoring club", "discount_percent": 10, "breakfast": True},
        {"code": "WEEK", "name": "Seven nights", "discount_percent": 15, "min_nights": 7},
    ],
}


@pytest.fixture
def hotel():
    return build_hotel(SETUP, MONDAY)


@pytest.fixture
def settings():
    return Settings()


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 3, 2, 14, 0))
