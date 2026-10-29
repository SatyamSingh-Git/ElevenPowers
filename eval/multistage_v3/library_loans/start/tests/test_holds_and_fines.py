from datetime import date

import pytest

from lending.errors import LendingError
from lending.model.holds import READY, WAITING
from lending.services import fines, holds
from lending.services.circulation import checkin, checkout
from lending.services.policy import due_date


def test_hold_on_a_title_with_a_free_copy_is_ready_at_once(at):
    hold = holds.place_hold(at(), 'M1001', 'T0002')
    assert hold.status == READY
    assert hold.barcode == '31000003'


def test_hold_queue_and_return(at):
    library = at()
    checkout(library, 'M1001', '31000004')
    first = holds.place_hold(library, 'M1002', 'T0003')
    second = holds.place_hold(library, 'C2001', 'T0003')
    assert (holds.position(library, first), holds.position(library, second)) == (1, 2)
    result = checkin(at(date(2026, 3, 6)), '31000004')
    assert result.hold.card == 'M1002'
    library = at(date(2026, 3, 6))
    with pytest.raises(LendingError) as raised:
        checkout(library, 'C2001', '31000004')
    assert raised.value.code == 'held_for_other'
    checkout(library, 'M1002', '31000004')
    assert [hold.card for hold in library.holds] == ['C2001']
    assert library.holds[0].status == WAITING


def test_duplicate_hold(at):
    library = at()
    holds.place_hold(library, 'M1001', 'T0002')
    with pytest.raises(LendingError) as raised:
        holds.place_hold(library, 'M1001', 'T0002')
    assert raised.value.message == 'M1001 already has a hold on T0002'


def test_uncollected_hold_lapses_to_the_next_member(at):
    library = at()
    holds.place_hold(library, 'M1001', 'T0002')
    holds.place_hold(library, 'C2001', 'T0002')
    assert holds.expire_holds(at(date(2026, 3, 9))) == []
    lapsed = holds.expire_holds(at(date(2026, 3, 10)))
    assert [hold.card for hold in lapsed] == ['M1001']
    ready = at(date(2026, 3, 10)).holds
    assert [(hold.card, hold.status, hold.ready_on) for hold in ready] == [('C2001', READY, date(2026, 3, 10))]


def test_fine_for_is_capped(at):
    library = at()
    loan = checkout(library, 'M1001', '31000004')
    assert fines.fine_for(library.settings, loan, 'DVD', 1999, date(2026, 3, 9)) == 0
    assert fines.fine_for(library.settings, loan, 'DVD', 1999, date(2026, 3, 12)) == 300
    assert fines.fine_for(library.settings, loan, 'DVD', 1999, date(2026, 4, 30)) == 1000
    assert fines.fine_for(library.settings, loan, 'DVD', 450, date(2026, 4, 30)) == 450


def test_balance_and_statement_come_from_the_ledger(at, ledger):
    ledger('2026-02-01 checkout 31000003 M1001 2026-02-22 0.00',
           '2026-03-01 return 31000003 M1001 2026-02-22 1.75',
           '2026-03-01 payment - M1001 - 1.00')
    library = at()
    assert fines.balance(library, 'M1001') == 75
    assert fines.balance(library, 'M1002') == 0
    lines = fines.statement(library, 'M1001')
    assert [(line.description, line.amount, line.owed) for line in lines] == [
        ('fine on 31000003', 175, 175), ('payment', -100, 75)]


def test_payment_is_recorded(at, ledger):
    ledger('2026-02-01 checkout 31000003 M1001 2026-02-22 0.00',
           '2026-03-01 return 31000003 M1001 2026-02-22 1.75')
    assert fines.pay(at(), 'M1001', 175) == 0
    assert fines.balance(at(), 'M1001') == 0


def test_payment_must_be_positive(at):
    with pytest.raises(LendingError) as raised:
        fines.pay(at(), 'M1001', 0)
    assert raised.value.code == 'bad_amount'


def test_waiver_cannot_exceed_balance(at, ledger):
    ledger('2026-02-01 checkout 31000003 M1001 2026-02-22 0.00',
           '2026-03-01 return 31000003 M1001 2026-02-22 1.75')
    with pytest.raises(LendingError) as raised:
        fines.waive(at(), 'M1001', 200)
    assert raised.value.message == 'cannot waive £2.00: M1001 owes £1.75'
    assert fines.waive(at(), 'M1001', 75) == 100


def test_amnesty_waives_only_older_charges(at, ledger):
    ledger('2026-01-01 checkout 31000003 M1001 2026-01-22 0.00',
           '2026-02-01 return 31000003 M1001 2026-01-22 2.50',
           '2026-02-02 checkout 31000004 M1001 2026-02-09 0.00',
           '2026-02-12 return 31000004 M1001 2026-02-09 3.00')
    assert fines.amnesty(at(), date(2026, 2, 10)) == {'M1001': 250}
    assert fines.balance(at(), 'M1001') == 300


def test_due_date_policy(at):
    library = at()
    assert due_date(library, 'AB', date(2026, 3, 2)) == date(2026, 3, 16)
