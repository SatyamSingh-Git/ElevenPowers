from dataclasses import replace
from datetime import date, datetime

import pytest

from parcelpost.core.clock import FixedClock
from parcelpost.core.errors import UnknownShipment, ValidationError
from parcelpost.services.booking import book, void
from parcelpost.storage.shipments import ShipmentStore


def test_booking_stores_the_shipment_and_writes_a_label(settings, clock, make_order):
    shipment = book(settings, make_order(), clock=clock)
    assert shipment.tracking_number == "PP000000019GB"
    assert shipment.service == "ground"
    assert shipment.ship_date == date(2026, 3, 2)
    assert shipment.expected_delivery == date(2026, 3, 5)
    stored = ShipmentStore(settings.store_path).get(shipment.tracking_number)
    assert stored == shipment
    label = (settings.labels_dir / "PP000000019GB.txt").read_text(encoding="utf-8")
    assert "SW1A 1AA" in label
    assert "PP000000019GB" in label


def test_sequence_continues_across_bookings(settings, clock, make_order):
    first = book(settings, make_order(), clock=clock)
    second = book(settings, make_order(account="BOLT"), clock=clock)
    assert (first.sequence, second.sequence) == (1, 2)


def test_late_booking_ships_next_business_day(settings, make_order):
    friday_evening = FixedClock(datetime(2026, 3, 6, 18, 30))
    shipment = book(settings, make_order(service="express"), clock=friday_evening)
    assert shipment.ship_date == date(2026, 3, 9)
    assert shipment.expected_delivery == date(2026, 3, 10)


def test_zpl_labels(settings, clock, make_order):
    settings = replace(settings, label_format="zpl")
    shipment = book(settings, make_order(signature=True), clock=clock)
    label = (settings.labels_dir / f"{shipment.tracking_number}.zpl").read_text(encoding="utf-8")
    assert label.startswith("^XA")
    assert "SIGNATURE REQUIRED" in label


def test_invalid_account(settings, clock, make_order):
    with pytest.raises(ValidationError, match="invalid account: acme"):
        book(settings, make_order(account="acme"), clock=clock)


def test_void_removes_a_booked_shipment(settings, clock, make_order):
    shipment = book(settings, make_order(), clock=clock)
    void(settings, shipment.tracking_number)
    with pytest.raises(UnknownShipment):
        ShipmentStore(settings.store_path).get(shipment.tracking_number)
    assert not (settings.labels_dir / f"{shipment.tracking_number}.txt").exists()


def test_void_refuses_manifested_shipments(settings, clock, make_order):
    shipment = book(settings, make_order(), clock=clock)
    store = ShipmentStore(settings.store_path)
    store.get(shipment.tracking_number).status = "manifested"
    store.save()
    with pytest.raises(ValidationError, match="only shipments not yet manifested can be voided"):
        void(settings, shipment.tracking_number)
