"""A full collection day through the Python API: book, close, bill, scan, report."""
from datetime import date, datetime

from parcelpost.config import load_settings
from parcelpost.core.address import make_address
from parcelpost.core.clock import FixedClock
from parcelpost.core.parcel import Parcel
from parcelpost.reports.daily import daily_summary
from parcelpost.reports.stalled import find_stalled
from parcelpost.services.billing import bill_day
from parcelpost.services.booking import Order, book
from parcelpost.services.manifesting import close_day
from parcelpost.services.scans import import_scans
from parcelpost.services.tracking import track

DAY = date(2026, 3, 2)
ORDERS = [
    ("ACME", "SW1A 1AA", Parcel(2500, 20, 15, 10), {}),
    ("BOLT", "LS1 4AP", Parcel(27000, 60, 40, 40), {"residential": True}),
    ("ACME", "G1 1AA", Parcel(1000, 20, 15, 10, declared_pence=30000), {"service": "express", "signature": True}),
    ("BOLT", "B1 1AA", Parcel(1000, 20, 15, 10), {}),
]


def _booked_day(tmp_path):
    settings = load_settings(tmp_path)
    clock = FixedClock(datetime(2026, 3, 2, 9, 0))
    shipments = [book(settings, Order(account, make_address("Pat Recipient", "1 Any Street", "Anytown", postcode),
                                      parcel, **options), clock=clock)
                 for account, postcode, parcel, options in ORDERS]
    close_day(settings, DAY)
    return settings, shipments


def _scans(*rows):
    return "tracking_number,code,date,time,depot\n" + "".join(",".join(row) + "\n" for row in rows)


def test_one_invoice_per_account_matching_the_bookings(tmp_path):
    settings, shipments = _booked_day(tmp_path)
    invoices = bill_day(settings, DAY)
    assert sorted(invoice.account for invoice in invoices) == ["ACME", "BOLT"]
    for invoice in invoices:
        mine = [shipment for shipment in shipments if shipment.account == invoice.account]
        assert sorted(charge.tracking_number for charge in invoice.charges) == sorted(
            shipment.tracking_number for shipment in mine)
        assert invoice.subtotal == sum(shipment.total for shipment in mine)
        assert invoice.total == invoice.subtotal + invoice.vat


def test_scans_reports_and_stalled(tmp_path):
    settings, shipments = _booked_day(tmp_path)
    numbers = [shipment.tracking_number for shipment in shipments]
    imported = import_scans(settings, _scans(
        *[(number, "PU", "2026-03-02", "18:00", "BHX") for number in numbers],
        (numbers[0], "OFD", "2026-03-04", "07:00", "LDN"),
        (numbers[2], "DL", "2026-03-03", "11:00", "GLA"),
    ))
    assert imported.scans == 6
    assert track(settings, numbers[1]).status == "in_transit"
    assert track(settings, numbers[2]).status == "delivered"

    summary = daily_summary(settings, DAY)
    assert summary.shipments == 4
    assert sum(summary.by_status.values()) == 4
    assert summary.revenue == sum(shipment.total for shipment in shipments)

    stalled = {row.tracking_number for row in find_stalled(settings, datetime(2026, 3, 9, 12, 0))}
    assert stalled == {numbers[0], numbers[1], numbers[3]}
