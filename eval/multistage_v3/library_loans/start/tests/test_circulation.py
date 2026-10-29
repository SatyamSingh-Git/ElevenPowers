from datetime import date
import json

import pytest

from lending.errors import LendingError
from lending.services.circulation import checkin, checkout, renew, write_off


def refused(code, action, *args):
    with pytest.raises(LendingError) as raised:
        action(*args)
    assert raised.value.code == code
    return raised.value.message


def test_checkout_sets_due_date_by_material(at):
    library = at()
    assert checkout(library, 'M1001', '31000001').due == date(2026, 3, 23)
    assert checkout(library, 'm1001', '31000004').due == date(2026, 3, 9)


def test_due_date_moves_off_closed_days(at, home):
    (home / 'lending.ini').write_text('[lending]\nclosed_days = mon\n', encoding='utf-8')
    assert checkout(at(), 'M1001', '31000001').due == date(2026, 3, 24)


def test_loans_survive_reopening(at):
    checkout(at(), 'M1001', '31000001')
    library = at(date(2026, 3, 5))
    assert library.loans['31000001'].due == date(2026, 3, 23)


def test_cannot_lend_a_copy_twice(at):
    library = at()
    checkout(library, 'M1001', '31000001')
    assert refused('on_loan', checkout, library, 'M1002', '31000001') == '31000001 is already on loan'


def test_unknown_member_and_copy(at):
    library = at()
    assert refused('unknown_member', checkout, library, 'M9999', '31000001') == 'no member with card M9999'
    assert refused('unknown_copy', checkout, library, 'M1001', '999') == 'no copy with barcode 999'


def test_child_loan_limit(at, home):
    titles = [{'id': f'T9{n:03d}', 'title': f'Picture book {n}', 'author': '', 'material': 'BK',
               'copies': [{'barcode': f'4100{n:04d}', 'branch': 'CEN', 'price': '5.00'}]} for n in range(11)]
    (home / 'catalogue.json').write_text(json.dumps({'titles': titles}), encoding='utf-8')
    library = at()
    for n in range(10):
        checkout(library, 'C2001', f'4100{n:04d}')
    message = refused('loan_limit', checkout, library, 'C2001', '41000010')
    assert message == 'C2001 has reached the loan limit of 10'


def test_renewal_runs_from_today(at):
    checkout(at(), 'M1001', '31000001')
    assert renew(at(date(2026, 3, 20)), '31000001').due == date(2026, 4, 10)


def test_renewal_limit(at):
    checkout(at(), 'M1001', '31000004')
    renew(at(date(2026, 3, 5)), '31000004')
    renew(at(date(2026, 3, 8)), '31000004')
    message = refused('renew_limit', renew, at(date(2026, 3, 10)), '31000004')
    assert message == '31000004 has already been renewed 2 times'


def test_return_on_time_costs_nothing(at):
    checkout(at(), 'M1001', '31000001')
    result = checkin(at(date(2026, 3, 23)), '31000001')
    assert result.fine == 0
    assert '31000001' not in at(date(2026, 3, 24)).loans


def test_late_return_is_fined_per_day(at):
    checkout(at(), 'M1001', '31000004')
    assert checkin(at(date(2026, 3, 14)), '31000004').fine == 500


def test_returning_what_is_not_out(at):
    assert refused('not_on_loan', checkin, at(), '31000001') == '31000001 is not on loan'


def test_member_who_owes_too_much_cannot_borrow(at, ledger):
    ledger('2026-02-01 checkout 31000003 M1001 2026-02-22 0.00',
           '2026-03-01 return 31000003 M1001 2026-02-22 6.00')
    message = refused('member_blocked', checkout, at(), 'M1001', '31000001')
    assert message == 'M1001 owes £6.00 and cannot borrow until it is paid'


def test_write_off_charges_the_price(at):
    checkout(at(), 'M1001', '31000003')
    library = at(date(2026, 5, 1))
    assert write_off(library, '31000003') == 999
    assert '31000003' in at(date(2026, 5, 2)).lost
    assert not at(date(2026, 5, 2)).is_free('31000003')


def test_return_at_another_branch_goes_into_transit(at):
    checkout(at(), 'M1001', '31000002')
    result = checkin(at(date(2026, 3, 10), branch='CEN'), '31000002')
    assert result.in_transit
    library = at(date(2026, 3, 11))
    assert not library.is_free('31000002')
