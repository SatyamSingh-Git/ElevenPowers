"""Manifest lines follow booking order, whatever the accounts."""
import csv
from datetime import date, datetime

from parcelpost.config import load_settings
from parcelpost.core.address import make_address
from parcelpost.core.clock import FixedClock
from parcelpost.core.parcel import Parcel
from parcelpost.services.booking import Order, book
from parcelpost.services.manifesting import close_day


def test_manifest_lines_are_in_booking_order(tmp_path):
    settings = load_settings(tmp_path)
    clock = FixedClock(datetime(2026, 3, 2, 9, 0))
    numbers = []
    for account in ("ZETA", "ACME", "ZETA", "BOLT", "ACME"):
        order = Order(account, make_address("Pat", "1 Any Street", "London", "SW1A 1AA"), Parcel(1000, 20, 15, 10))
        numbers.append(book(settings, order, clock=clock).tracking_number)
    close_day(settings, date(2026, 3, 2))
    with open(tmp_path / "manifests" / "manifest-2026-03-02.csv", newline="", encoding="utf-8") as handle:
        assert [row["tracking_number"] for row in csv.DictReader(handle)] == numbers
