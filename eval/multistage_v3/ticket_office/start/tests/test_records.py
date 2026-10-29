import json

import pytest

from boxoffice.errors import BoxOfficeError
from boxoffice.storage.backup import create_backup, list_backups, restore_backup
from boxoffice.storage.migrations import upgrade


def test_customer_book(office):
    office.customers.add("ann@example.com", "Ann Lee", "01632 960001", mailing_list=True)
    office.customers.add("bob@example.com", "Bob Stone")
    assert [c.email for c in office.customers.search("lee")] == ["ann@example.com"]
    assert [c.email for c in office.customers.search("960001")] == ["ann@example.com"]
    assert office.customers.mailing_list() == ["ann@example.com"]
    with pytest.raises(BoxOfficeError) as raised:
        office.customers.add("ANN@example.com", "Ann Again")
    assert raised.value.code == "duplicate-customer"


def test_waitlist_offers_seats_to_parties_that_fit(office):
    for n in range(1, 7):
        office.sales.checkout(office.holds.place("TEMP-0520", [f"A{n}"]).id)
    office.sales.checkout(office.holds.place("TEMP-0520", [f"B{n}" for n in range(1, 7)]).id)
    office.sales.checkout(office.holds.place("TEMP-0520", ["C1", "C2"]).id)
    office.waitlist.join("TEMP-0520", "ann@example.com", 3)
    office.waitlist.join("TEMP-0520", "bob@example.com", 2)
    assert [entry["email"] for entry in office.waitlist.to_contact("TEMP-0520")] == ["bob@example.com"]
    office.waitlist.leave("TEMP-0520", "bob@example.com")
    assert office.waitlist.queue("TEMP-0520") == [{"email": "ann@example.com", "seats": 3}]


def test_backup_and_restore(office):
    create_backup(office.root, "before")
    office.sales.checkout(office.holds.place("TEMP-0520", ["A1"]).id)
    assert list_backups(office.root) == ["before"]
    restore_backup(office.root, "before")
    assert office.store.load_orders() == {}
    assert not (office.root / "ledger.jsonl").exists()


def test_upgrade_old_files(tmp_path):
    (tmp_path / "orders.json").write_text(json.dumps({"B0001": {"performance": "X"}}))
    (tmp_path / "holds.json").write_text(json.dumps({"H0001": {"order": "B0001"}}))
    assert upgrade(tmp_path) == ["orders.json", "holds.json"]
    assert json.loads((tmp_path / "holds.json").read_text())["H0001"]["status"] == "sold"
    assert upgrade(tmp_path) == []


def test_settings_file(tmp_path, clock):
    from boxoffice.config import SettingsError, load_settings
    (tmp_path / "boxoffice.ini").write_text("[boxoffice]\nbooking_fee = 200\ntheatre = The Lyric\n")
    settings = load_settings(tmp_path)
    assert (settings.booking_fee, settings.theatre, settings.hold_minutes) == (200, "The Lyric", 15)
    (tmp_path / "boxoffice.ini").write_text("[boxoffice]\nbooking_fees = 200\n")
    with pytest.raises(SettingsError):
        load_settings(tmp_path)
