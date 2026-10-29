import csv
from datetime import datetime
from decimal import Decimal

from clinicbook.services.fees import by_patient, charges, total, write_charges
from conftest import MONDAY, at


def test_each_no_show_is_charged_the_fee(desk, clock, clinic):
    first = desk.book("amy", MONDAY, at("14:00"), "Ann Lee", "07700900001")
    second = desk.book("amy", MONDAY, at("09:00"), "Bob Ray", "07700900002")
    came = desk.book("ben", MONDAY, at("09:00"), "Cy Tan", "07700900003")
    clock.moment = datetime(2026, 3, 2, 18, 0)
    desk.mark_no_show(first.id)
    desk.mark_no_show(second.id)
    desk.mark_attended(came.id)
    owed = charges(desk.bookings, clinic.settings)
    assert [charge.booking for charge in owed] == ["B0001", "B0002"]
    assert {charge.amount for charge in owed} == {Decimal("25.00")}
    assert total(owed) == Decimal("50.00")
    assert set(by_patient(owed)) == {"07700900001", "07700900002"}


def test_charges_file(desk, clock, clinic, tmp_path):
    booking = desk.book("amy", MONDAY, at("09:00"), "Ann Lee", "07700900001")
    clock.moment = datetime(2026, 3, 2, 18, 0)
    desk.mark_no_show(booking.id)
    path = tmp_path / "charges.csv"
    write_charges(charges(desk.bookings, clinic.settings), path)
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows == [
        ["booking", "patient", "phone", "day", "reason", "amount"],
        ["B0001", "Ann Lee", "07700900001", "2026-03-02", "no-show", "25.00"],
    ]
