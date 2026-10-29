"""Stage 6: day_statistics() gives occupancy as a percentage to two decimals."""
from datetime import date

from hoteldesk.config import Settings
from hoteldesk.services import booking, housekeeping
from hoteldesk.services.inventory import day_statistics
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"}],
    "rooms": [{"number": str(number), "type": "QN"} for number in range(101, 106)],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def _booked(count):
    hotel = build_hotel(SETUP, MONDAY)
    for n in range(count):
        booking.book(hotel, Settings(), guest=f"Guest {n}", room_type="QN", arrival=MONDAY,
                     departure=date(2026, 3, 3))
    return hotel


def test_two_of_five():
    stats = day_statistics(_booked(2), MONDAY)
    assert stats["occupancy"] == 40.0
    assert (stats["sold"], stats["available"]) == (2, 5)


def test_one_of_three_rounds_to_two_decimals():
    hotel = _booked(1)
    housekeeping.set_status(hotel, "104", "out_of_order")
    housekeeping.set_status(hotel, "105", "out_of_order")
    assert day_statistics(hotel, MONDAY)["occupancy"] == 33.33


def test_full_and_empty():
    assert day_statistics(_booked(5), MONDAY)["occupancy"] == 100.0
    assert day_statistics(_booked(0), MONDAY)["occupancy"] == 0.0
