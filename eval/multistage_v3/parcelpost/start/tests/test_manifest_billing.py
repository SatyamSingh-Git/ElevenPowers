from datetime import date
from decimal import Decimal

import pytest

from parcelpost.core.accounts import make_account
from parcelpost.core.errors import ManifestError
from parcelpost.core.shipment import MANIFESTED
from parcelpost.services.billing import Charge, invoice_number, make_invoices
from parcelpost.services.booking import book
from parcelpost.services.manifesting import close_day
from parcelpost.storage.accounts import AccountBook
from parcelpost.storage.shipments import ShipmentStore

DAY = date(2026, 3, 2)


def test_close_day_writes_the_manifest(settings, clock, make_order):
    book(settings, make_order(account="BOLT"), clock=clock)
    book(settings, make_order(account="ACME", residential=True), clock=clock)
    closed = close_day(settings, DAY)
    assert closed.shipments == 2
    lines = closed.path.read_text(encoding="utf-8").splitlines()
    assert lines == [
        "tracking_number,account,service,zone,weight_g,billable_g,charge,surcharges",
        "PP000000028GB,ACME,ground,4,2500,2500,1140,residential",
        "PP000000019GB,BOLT,ground,4,2500,2500,763,",
    ]
    statuses = {shipment.status for shipment in ShipmentStore(settings.store_path).find()}
    assert statuses == {MANIFESTED}


def test_a_day_closes_once(settings, clock, make_order):
    book(settings, make_order(), clock=clock)
    close_day(settings, DAY)
    with pytest.raises(ManifestError, match="manifest for 2026-03-02 is already closed"):
        close_day(settings, DAY)


def test_nothing_to_manifest(settings):
    with pytest.raises(ManifestError, match="no shipments to manifest for 2026-03-02"):
        close_day(settings, DAY)


def test_invoices_per_account_with_vat(tmp_path):
    charges = [
        Charge("PP000000019GB", "ACME", "ground", 763),
        Charge("PP000000037GB", "ACME", "express", 1817),
        Charge("PP000000028GB", "BOLT", "ground", 3429),
    ]
    accounts = AccountBook(tmp_path / "accounts.json")
    accounts.add(make_account("ACME", "Acme Ltd", "ops@acme.test", payment_days=14))
    invoices = make_invoices(DAY, charges, Decimal("20"), accounts)
    assert [(invoice.account, invoice.subtotal, invoice.vat, invoice.total) for invoice in invoices] == [
        ("ACME", 2580, 516, 3096),
        ("BOLT", 3429, 686, 4115),
    ]
    assert invoices[0].customer == "Acme Ltd"
    assert invoices[0].due == date(2026, 3, 16)
    assert invoices[1].due == date(2026, 4, 1)


def test_invoice_number():
    assert invoice_number("ACME", DAY) == "INV-ACME-20260302"
