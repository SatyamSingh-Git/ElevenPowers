from datetime import date

import pytest

from lending.errors import LendingError
from lending.model.isbn import is_valid_isbn, normalise_isbn, to_isbn13
from lending.reports.day_sheet import day_sheet
from lending.reports.demand import demand_rows
from lending.services import cataloguing, holds
from lending.services.circulation import checkout


@pytest.mark.parametrize('text, valid', [
    ('0-261-10334-2', True), ('978-0-261-10334-4', True), ('080442957X', True),
    ('0-261-10334-3', False), ('9780261103345', False), ('12345', False),
])
def test_isbn_check_digits(text, valid):
    assert is_valid_isbn(normalise_isbn(text)) is valid


def test_both_forms_of_an_isbn_match():
    assert to_isbn13('0261103342') == '9780261103344'


def test_cataloguing_a_title_and_finding_it_by_isbn(at):
    added = cataloguing.add_title(at(), 'The Silmarillion', 'J. R. R. Tolkien', 'bk', '978-0-261-10273-6')
    assert added.id == 'T0006'
    cataloguing.add_copy(at(), added.id, '31000099', 'riv', 1099)
    library = at()
    assert [title.id for title in library.catalogue.search('0261102737')] == ['T0006']
    assert library.copy('31000099').price == 1099


def test_an_isbn_is_catalogued_once(at):
    cataloguing.add_title(at(), 'The Silmarillion', '', 'BK', '9780261102736')
    with pytest.raises(LendingError) as raised:
        cataloguing.add_title(at(), 'The Silmarillion (again)', '', 'BK', '0-261-10273-7')
    assert raised.value.message == 'catalogue: ISBN 0261102737 is already catalogued'


def test_withdrawing_a_copy_on_loan_is_refused(at):
    checkout(at(), 'M1001', '31000003')
    with pytest.raises(LendingError) as raised:
        cataloguing.withdraw(at(), '31000003')
    assert raised.value.code == 'on_loan'


def test_demand(at):
    checkout(at(), 'M1001', '31000003')
    holds.place_hold(at(), 'M1002', 'T0002')
    holds.place_hold(at(), 'C2001', 'T0002')
    assert demand_rows(at()) == [
        {'id': 'T0002', 'title': 'Dune', 'material': 'Book', 'copies': 1, 'waiting': 2, 'per_copy': '2.0'}]


def test_day_sheet(at, ledger):
    ledger('2026-03-01 checkout 31000004 M1001 2026-03-08 0.00',
           '2026-03-14 return 31000004 M1001 2026-03-08 6.00',
           '2026-03-14 payment - M1001 - 2.00')
    checkout(at(date(2026, 3, 14)), 'M1002', '31000004')
    sheet = day_sheet(at(date(2026, 3, 14)), date(2026, 3, 14))
    assert 'issued: 1\nreturned: 1\n' in sheet
    assert 'charged: £6.00\ntaken: £2.00\n' in sheet
