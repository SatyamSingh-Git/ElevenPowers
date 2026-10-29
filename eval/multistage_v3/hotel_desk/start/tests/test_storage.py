from datetime import date, timedelta
import json

import pytest

from hoteldesk.config import load_settings
from hoteldesk.errors import NotFound, ValidationError
from hoteldesk.services import billing, booking, guests, stays
from hoteldesk.storage import backups, channel_import, folio_export, setup, state

from conftest import SETUP

MONDAY = date(2026, 3, 2)


def test_state_round_trip(hotel, settings, clock, tmp_path):
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    stays.check_in(hotel, clock, reservation.id)
    billing.post_charge(hotel, reservation.id, "MB", 800)
    guests.save_profile(hotel, "Ann Lee", email="ann@example.com", vip=True)
    path = tmp_path / "hotel-state.json"
    state.save_hotel(hotel, path)
    assert state.load_hotel(path) == hotel


def test_missing_state_file(tmp_path):
    with pytest.raises(NotFound, match="run `hoteldesk init` first"):
        state.load_hotel(tmp_path / "nope.json")


def test_setup_rejects_unknown_room_type():
    broken = {**SETUP, "rooms": [{"number": "101", "type": "XX"}]}
    with pytest.raises(ValidationError, match="Room 101 has unknown type XX"):
        setup.build_hotel(broken, MONDAY)


def test_floor_comes_from_the_room_number(hotel):
    assert hotel.room("201").floor == 2


def test_setup_export_reloads(hotel, tmp_path):
    path = tmp_path / "setup.json"
    setup.export_setup(hotel, path)
    again = setup.load_setup(path, MONDAY)
    assert again.rooms == hotel.rooms and again.room_types == hotel.room_types


def test_settings_file(tmp_path):
    path = tmp_path / "hotel.json"
    path.write_text(json.dumps({"check_out_time": "12:00", "late_checkout_fee": "30.00"}))
    settings = load_settings(path)
    assert settings.check_out_time.hour == 12 and settings.late_checkout_fee == 3000
    assert load_settings(tmp_path / "absent.json").max_stay_nights == 30


def test_unknown_setting(tmp_path):
    path = tmp_path / "hotel.json"
    path.write_text(json.dumps({"checkout": "12:00"}))
    with pytest.raises(ValidationError, match="Unknown setting: checkout"):
        load_settings(path)


def test_channel_import(hotel, settings, tmp_path):
    path = tmp_path / "channel.csv"
    path.write_text(
        "channel_ref,guest,room_type,arrival,departure,adults,rate_plan\n"
        "BK-1,Ann Lee,QN,2026-03-02,2026-03-04,2,\n"
        "BK-2,Bo Chen,ST,2026-03-03,2026-03-02,1,BAR\n"
        "BK-1,Ann Lee,QN,2026-03-02,2026-03-04,2,\n"
    )
    result = channel_import.import_bookings(hotel, settings, path)
    assert result.booked == ["R0001"]
    assert result.rejected == [(3, "Departure must be after arrival"), (4, "Duplicate channel reference BK-1")]
    assert hotel.reservation("R0001").source == "channel:BK-1"


def test_channel_import_needs_every_column(hotel, settings, tmp_path):
    path = tmp_path / "channel.csv"
    path.write_text("channel_ref,guest\nBK-1,Ann Lee\n")
    with pytest.raises(ValidationError, match="missing columns: room_type, arrival"):
        channel_import.import_bookings(hotel, settings, path)


def test_folio_export(hotel, settings, clock, tmp_path):
    reservation = booking.book(hotel, settings, guest="Ann Lee", room_type="QN", arrival=MONDAY,
                               departure=date(2026, 3, 4))
    stays.check_in(hotel, clock, reservation.id)
    billing.post_charge(hotel, reservation.id, "FB", 2000)
    path = tmp_path / "folios.csv"
    assert folio_export.export_folios(hotel, path) == 2
    assert path.read_text().splitlines() == [
        "reservation,guest,date,code,description,amount",
        "R0001,Ann Lee,2026-03-02,FB,Food and beverage,20.00",
        "R0001,Ann Lee,2026-03-02,TAX,Tax on Food and beverage,1.45",
    ]


def test_backups_keep_the_latest(tmp_path):
    path = tmp_path / "hotel-state.json"
    path.write_text("{}")
    for offset in range(backups.KEEP + 2):
        backups.take_backup(path, MONDAY + timedelta(days=offset))
    kept = backups.list_backups(path)
    assert len(kept) == backups.KEEP
    assert kept[0].name == "hotel-state-2026-03-04.json"
