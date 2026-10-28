"""With no setting, a shipment stalls after 24 hours without a scan; an explicit setting still wins."""
from datetime import date, datetime

from parcelpost.config import load_settings
from parcelpost.core.address import make_address
from parcelpost.core.clock import FixedClock
from parcelpost.core.parcel import Parcel
from parcelpost.reports.stalled import find_stalled
from parcelpost.services.booking import Order, book
from parcelpost.services.manifesting import close_day
from parcelpost.services.scans import import_scans


def _scanned(tmp_path):
    settings = load_settings(tmp_path)
    shipment = book(settings, Order("ACME", make_address("Pat", "1 Any Street", "London", "SW1A 1AA"),
                                    Parcel(1000, 20, 15, 10)), clock=FixedClock(datetime(2026, 3, 2, 9, 0)))
    close_day(settings, date(2026, 3, 2))
    import_scans(settings, "tracking_number,code,date,time,depot\n"
                           f"{shipment.tracking_number},PU,2026-03-02,18:00,BHX\n")
    return shipment.tracking_number


def test_default_is_twenty_four_hours(tmp_path):
    number = _scanned(tmp_path)
    settings = load_settings(tmp_path)
    assert settings.stale_hours == 24
    assert [row.tracking_number for row in find_stalled(settings, datetime(2026, 3, 4, 0, 0))] == [number]
    assert find_stalled(settings, datetime(2026, 3, 3, 12, 0)) == []


def test_an_explicit_setting_is_kept(tmp_path):
    _scanned(tmp_path)
    (tmp_path / "parcelpost.ini").write_text("[parcelpost]\nstale_hours = 48\n", encoding="utf-8")
    settings = load_settings(tmp_path)
    assert settings.stale_hours == 48
    assert find_stalled(settings, datetime(2026, 3, 4, 0, 0)) == []
