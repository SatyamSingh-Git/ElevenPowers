"""Stage 7: cancelled_retention_days is a setting the settings file can change."""
from datetime import date
import json

import pytest

from hoteldesk.config import load_settings
from hoteldesk.errors import NotFound
from hoteldesk.services import booking, night_audit
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"}],
    "rooms": [{"number": "101", "type": "QN"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def test_default_from_a_settings_file_without_it(tmp_path):
    path = tmp_path / "hotel.json"
    path.write_text(json.dumps({"check_out_time": "11:30"}))
    assert load_settings(path).cancelled_retention_days == 30


def test_shorter_retention(tmp_path):
    path = tmp_path / "hotel.json"
    path.write_text(json.dumps({"cancelled_retention_days": 7}))
    settings = load_settings(path)
    assert settings.cancelled_retention_days == 7
    hotel = build_hotel(SETUP, MONDAY)
    cancelled = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                             departure=date(2026, 3, 3))
    booking.cancel(hotel, cancelled.id)
    while hotel.business_date <= date(2026, 3, 10):
        night_audit.run_audit(hotel, settings)
    assert hotel.reservation(cancelled.id).status == "cancelled"
    night_audit.run_audit(hotel, settings)
    with pytest.raises(NotFound):
        hotel.reservation(cancelled.id)
