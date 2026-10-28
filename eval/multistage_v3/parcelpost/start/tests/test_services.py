from datetime import date, datetime

import pytest

from parcelpost.config import load_settings
from parcelpost.core.clock import FixedClock
from parcelpost.core.errors import ConfigError, ValidationError
from parcelpost.formats.carrier_invoice import parse_carrier_invoice
from parcelpost.formats.events import Event, append_events
from parcelpost.reports.export import export_shipments
from parcelpost.reports.performance import on_time_performance
from parcelpost.services.booking import book
from parcelpost.services.claims import compensation, raise_claim
from parcelpost.services.importer import import_orders
from parcelpost.services.returns import RETURNS_ADDRESS, book_return
from parcelpost.storage.shipments import ShipmentStore

ORDERS = """account,name,line1,town,postcode,weight_kg,size_cm,service,residential,signature,value
acme,Ann Example,1 High Street,London,sw1a1aa,2.5,20x15x10,,yes,,
bolt,Bob Example,2 Low Road,Leeds,LS1 4AP,1,20x15x10,express,,,50.00
acme,Cat Example,3 Mid Lane,Nowhere,XX1 1XX,1,20x15x10,,,,
"""


def _deliver(settings, shipment, at):
    append_events(settings.events_path, [Event(shipment.tracking_number, "DL", at, "LDN")])
    store = ShipmentStore(settings.store_path)
    store.get(shipment.tracking_number).status = "delivered"
    store.save()


def test_settings_file_overrides_defaults(tmp_path):
    (tmp_path / "parcelpost.ini").write_text("[parcelpost]\nfuel_percent = 9\ncutoff = 15:30\n")
    settings = load_settings(tmp_path)
    assert str(settings.fuel_percent) == "9"
    assert settings.cutoff.hour == 15
    assert settings.stale_hours == 48


@pytest.mark.parametrize("line, message", [
    ("colour = red", "unknown setting: colour"),
    ("stale_hours = soon", "invalid value for stale_hours: soon"),
    ("label_format = pdf", "invalid value for label_format: pdf"),
])
def test_bad_settings(tmp_path, line, message):
    (tmp_path / "parcelpost.ini").write_text(f"[parcelpost]\n{line}\n")
    with pytest.raises(ConfigError, match=message):
        load_settings(tmp_path)


def test_import_orders_books_what_it_can(settings, clock):
    report = import_orders(settings, ORDERS, clock=clock)
    assert [(shipment.account, shipment.service, shipment.residential) for shipment in report.booked] == [
        ("ACME", "ground", True),
        ("BOLT", "express", False),
    ]
    assert report.errors == [(4, "no service to postcode area XX")]


def test_import_orders_needs_its_columns(settings, clock):
    with pytest.raises(ValidationError, match="orders file is missing columns: size_cm"):
        import_orders(settings, "account,name,line1,town,postcode,weight_kg\n", clock=clock)


def test_returns_go_back_to_the_depot(settings, clock, make_order):
    shipment = book(settings, make_order(), clock=clock)
    with pytest.raises(ValidationError, match="only delivered shipments can be returned"):
        book_return(settings, shipment.tracking_number, clock=clock)
    _deliver(settings, shipment, datetime(2026, 3, 4, 11, 0))
    returned = book_return(settings, shipment.tracking_number, clock=clock)
    assert returned.recipient == RETURNS_ADDRESS
    assert returned.service == "economy"
    assert returned.return_of == shipment.tracking_number
    with pytest.raises(ValidationError, match="already has return"):
        book_return(settings, shipment.tracking_number, clock=clock)


def test_claims(settings, clock, make_order):
    insured = book(settings, make_order(declared_pence=40_000), clock=clock)
    plain = book(settings, make_order(), clock=clock)
    assert compensation(insured) == 40_000
    assert compensation(plain) == 2000
    with pytest.raises(ValidationError, match="damage can only be claimed after delivery"):
        raise_claim(settings, plain.tracking_number, "damaged", clock=clock)
    later = FixedClock(datetime(2026, 3, 20, 9, 0))
    claim = raise_claim(settings, plain.tracking_number, "lost", clock=later)
    assert (claim.number, claim.pence) == ("CLM-00001", 2000)


def test_on_time_performance(settings, clock, make_order):
    early = book(settings, make_order(), clock=clock)
    late = book(settings, make_order(), clock=clock)
    _deliver(settings, early, datetime(2026, 3, 5, 15, 0))
    _deliver(settings, late, datetime(2026, 3, 6, 9, 0))
    [ground] = on_time_performance(settings, date(2026, 3, 1), date(2026, 3, 31))
    assert (ground.service, ground.delivered, ground.on_time, ground.percent) == ("ground", 2, 1, 50.0)


def test_export(settings, clock, make_order):
    book(settings, make_order(), clock=clock)
    lines = export_shipments(settings, date(2026, 3, 1), date(2026, 3, 31)).splitlines()
    assert lines[0] == "tracking_number,account,service,booked_at,ship_date,status,charge,return_of"
    assert lines[1].endswith(",booked,7.63,")


def test_carrier_invoice():
    assert parse_carrier_invoice("tracking_number,amount\npp000000019gb,7.63\n") == {"PP000000019GB": 763}
    with pytest.raises(ValidationError, match="charged twice"):
        parse_carrier_invoice("tracking_number,amount\nPP1,1.00\nPP1,1.00\n")
