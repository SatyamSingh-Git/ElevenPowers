"""An OFD scan sets out_for_delivery; a later delivery scan still delivers."""
from datetime import date, datetime

from parcelpost.config import load_settings
from parcelpost.core.address import make_address
from parcelpost.core.clock import FixedClock
from parcelpost.core.parcel import Parcel
from parcelpost.services.booking import Order, book
from parcelpost.services.manifesting import close_day
from parcelpost.services.scans import import_scans
from parcelpost.services.tracking import track

HEADER = "tracking_number,code,date,time,depot\n"


def test_ofd_scan_sets_out_for_delivery(tmp_path):
    settings = load_settings(tmp_path)
    clock = FixedClock(datetime(2026, 3, 2, 9, 0))
    shipment = book(settings, Order("ACME", make_address("Pat", "1 Any Street", "London", "SW1A 1AA"),
                                    Parcel(2500, 20, 15, 10)), clock=clock)
    other = book(settings, Order("ACME", make_address("Sam", "2 Any Street", "Leeds", "LS1 4AP"),
                                 Parcel(1000, 20, 15, 10)), clock=clock)
    close_day(settings, date(2026, 3, 2))
    number = shipment.tracking_number
    import_scans(settings, HEADER + f"{number},PU,2026-03-02,18:00,BHX\n{other.tracking_number},PU,2026-03-02,18:00,BHX\n"
                 f"{number},OFD,2026-03-04,07:10,LDN\n")
    assert track(settings, number).status == "out_for_delivery"
    assert track(settings, other.tracking_number).status == "in_transit"
    import_scans(settings, HEADER + f"{number},DL,2026-03-04,12:30,LDN\n")
    assert track(settings, number).status == "delivered"
