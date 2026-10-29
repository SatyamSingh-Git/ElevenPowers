"""Stage 4: nightly room charges are posted under ROOM."""
import csv
from datetime import date, datetime

from hoteldesk.clock import FixedClock
from hoteldesk.config import Settings
from hoteldesk.services import booking, night_audit, stays
from hoteldesk.storage.folio_export import export_folios
from hoteldesk.storage.setup import build_hotel

MONDAY = date(2026, 3, 2)
SETUP = {
    "name": "Harbour View Inn",
    "room_types": [{"code": "QN", "name": "Queen", "max_adults": 2, "base_rate": "120.00"}],
    "rooms": [{"number": "101", "type": "QN"}, {"number": "102", "type": "QN"}],
    "rate_plans": [{"code": "BAR", "name": "Best available"}],
}


def _two_nights():
    hotel = build_hotel(SETUP, MONDAY)
    settings = Settings()
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    stays.check_in(hotel, FixedClock(datetime(2026, 3, 2, 15, 0)), reservation.id)
    night_audit.run_audit(hotel, settings)
    result = night_audit.run_audit(hotel, settings)
    return hotel, reservation, result


def test_night_audit_posts_room_code():
    hotel, reservation, result = _two_nights()
    charges = hotel.folio(reservation.id).charges
    assert [c.code for c in charges] == ["ROOM", "TAX", "ROOM", "TAX"]
    assert result.room_revenue == 12000 and result.tax_revenue == 1410


def test_folio_export_carries_room_code(tmp_path):
    hotel, reservation, _ = _two_nights()
    path = tmp_path / "folios.csv"
    export_folios(hotel, path)
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["code"] for row in rows] == ["ROOM", "TAX", "ROOM", "TAX"]
    assert [row["amount"] for row in rows if row["code"] == "ROOM"] == ["120.00", "120.00"]
