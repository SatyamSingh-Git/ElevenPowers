"""The manifest's charge column is pounds with two decimals."""
import csv
from datetime import date, datetime

from parcelpost.config import load_settings
from parcelpost.core.address import make_address
from parcelpost.core.clock import FixedClock
from parcelpost.core.parcel import Parcel
from parcelpost.services.booking import Order, book
from parcelpost.services.manifesting import close_day


def test_manifest_charges_are_pounds(tmp_path):
    settings = load_settings(tmp_path)
    clock = FixedClock(datetime(2026, 3, 2, 9, 0))
    orders = [
        Order("ACME", make_address("Pat", "1 Any Street", "London", "SW1A 1AA"), Parcel(2500, 20, 15, 10)),
        Order("BOLT", make_address("Sam", "2 Any Street", "Birmingham", "B1 1AA"), Parcel(1000, 20, 15, 10),
              residential=True),
        Order("ACME", make_address("Lee", "3 Any Street", "Glasgow", "G1 1AA"), Parcel(1000, 20, 15, 10),
              service="express"),
    ]
    shipments = [book(settings, order, clock=clock) for order in orders]
    close_day(settings, date(2026, 3, 2))
    with open(tmp_path / "manifests" / "manifest-2026-03-02.csv", newline="", encoding="utf-8") as handle:
        charges = {row["tracking_number"]: row["charge"] for row in csv.DictReader(handle)}
    assert len(charges) == 3
    for shipment in shipments:
        assert charges[shipment.tracking_number] == f"{shipment.total // 100}.{shipment.total % 100:02d}"
