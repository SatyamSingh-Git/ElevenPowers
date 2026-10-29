import pytest

from boxoffice.errors import BoxOfficeError


def test_checkout_prices_seats_and_charges_one_fee(office):
    hold = office.holds.place("TEMP-0520", ["A1", "A2", "C1"])
    order = office.sales.checkout(hold.id, {"A2": "child"}, payment="cash")
    assert order.id == "B0001"
    assert [(line.seat, line.concession, line.price) for line in order.lines] == [
        ("A1", "adult", 3000), ("A2", "child", 1500), ("C1", "adult", 2000)]
    assert order.fee == 150
    assert order.total == 6650
    assert office.seat_states("TEMP-0520")["A2"] == "sold"


def test_checkout_records_the_sale(office):
    hold = office.holds.place("TEMP-0520", ["A1"])
    office.sales.checkout(hold.id)
    [entry] = office.ledger.read_entries()
    assert entry["kind"] == "sale"
    assert entry["amount"] == 3150
    assert entry["tickets"] == 1
    assert entry["payment"] == "card"


def test_a_hold_sells_once(office):
    hold = office.holds.place("TEMP-0520", ["A1"])
    office.sales.checkout(hold.id)
    with pytest.raises(BoxOfficeError) as raised:
        office.sales.checkout(hold.id)
    assert raised.value.code == "hold-closed"


def test_unknown_payment(office):
    hold = office.holds.place("TEMP-0520", ["A1"])
    with pytest.raises(BoxOfficeError) as raised:
        office.sales.checkout(hold.id, payment="cheque")
    assert str(raised.value) == "unknown payment method cheque"


def test_concession_for_a_seat_outside_the_hold(office):
    hold = office.holds.place("TEMP-0520", ["A1"])
    with pytest.raises(BoxOfficeError) as raised:
        office.sales.checkout(hold.id, {"A2": "child"})
    assert str(raised.value) == "seat A2 is not in hold H0001"


def test_customer_is_recorded(office):
    office.customers.add("Ann@Example.com", "Ann Lee")
    hold = office.holds.place("TEMP-0520", ["A1"])
    order = office.sales.checkout(hold.id, customer="ann@example.com")
    assert office.order(order.id).customer == "ann@example.com"


def test_occupied_seat_map_is_consistent(office):
    for seats in (["A1", "A2"], ["C1"]):
        office.sales.checkout(office.holds.place("TEMP-0520", seats).id)
    assert office.check() == []
