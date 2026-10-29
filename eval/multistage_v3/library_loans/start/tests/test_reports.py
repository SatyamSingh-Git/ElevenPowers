from datetime import date
import json

from lending.reports.activity import activity_rows
from lending.reports.loans import member_loans
from lending.reports.overdue import overdue_rows
from lending.reports.render import render
from lending.reports.search import search_rows
from lending.reports.stock import collection_rows, popular_rows
from lending.services.accounts import summary
from lending.services.circulation import checkin, checkout, renew
from lending.services.fines import pay


def test_overdue_report(at):
    library = at()
    checkout(library, 'M1001', '31000001')
    checkout(library, 'M1002', '31000004')
    rows = overdue_rows(at(date(2026, 4, 2)))
    assert [(row['barcode'], row['days'], row['accrued']) for row in rows] == [
        ('31000004', 24, '£10.00'), ('31000001', 10, '£2.50')]


def test_activity_by_month(at, ledger):
    ledger('2026-02-01 checkout 31000003 M1001 2026-02-22 0.00',
           '2026-03-01 payment - M1002 - 1.00')
    library = at()
    checkout(library, 'M1001', '31000001')
    renew(at(date(2026, 3, 10)), '31000001')
    checkin(at(date(2026, 3, 20)), '31000001')
    pay(at(date(2026, 3, 20)), 'M1001', 50)
    rows = activity_rows(at(date(2026, 3, 21)).ledger.entries(), 2026)
    assert rows == [
        {'month': '2026-02', 'issues': 1, 'renewals': 0, 'returns': 0, 'lost': 0, 'payments': 0, 'waivers': 0,
         'taken': '£0.00'},
        {'month': '2026-03', 'issues': 1, 'renewals': 1, 'returns': 1, 'lost': 0, 'payments': 2, 'waivers': 0,
         'taken': '£1.50'},
    ]


def test_member_loans(at):
    library = at()
    checkout(library, 'M1001', '31000001')
    checkout(library, 'M1001', '31000004')
    renew(at(date(2026, 3, 5)), '31000004')
    renew(at(date(2026, 3, 8)), '31000004')
    rows = member_loans(at(date(2026, 3, 20)), 'M1001')
    assert [(row['barcode'], row['overdue'], row['renewals_left'], row['renewable']) for row in rows] == [
        ('31000004', 5, 0, 'no'), ('31000001', 0, 2, 'yes')]


def test_account_summary(at):
    library = at()
    checkout(library, 'M1001', '31000001')
    checkout(library, 'M1001', '31000003')
    found = summary(at(date(2026, 3, 25)), 'M1001')
    assert (found.on_loan, found.overdue, found.owed, found.can_borrow) == (2, 2, 0, 18)


def test_search_shows_what_is_on_the_shelf(at):
    library = at()
    checkout(library, 'M1001', '31000001')
    rows = search_rows(library, 'hobbit')
    assert [(row['id'], row['copies'], row['available']) for row in rows] == [('T0001', 2, 1)]
    assert [row['id'] for row in search_rows(library, 'the')] == ['T0004', 'T0001']


def test_collection_and_popular(at):
    library = at()
    checkout(library, 'M1001', '31000001')
    checkin(at(date(2026, 3, 3)), '31000001')
    checkout(at(date(2026, 3, 4)), 'M1002', '31000002')
    library = at(date(2026, 3, 5))
    rows = collection_rows(library)
    assert rows[0] == {'branch': 'Central', 'material': 'Book', 'copies': 2, 'on_loan': 0, 'lost': 0,
                       'value': '£18.98'}
    assert popular_rows(library, date(2026, 3, 1), date(2026, 3, 31))[0] == {
        'rank': 1, 'id': 'T0001', 'title': 'The Hobbit', 'issues': 2}


def test_render_formats():
    rows = [{'a': 1, 'b': 'x'}, {'a': 22, 'b': 'y'}]
    assert render(rows, ('a', 'b')) == 'a   b\n--  -\n1   x\n22  y\n'
    assert render(rows, ('b',), 'csv') == 'b\nx\ny\n'
    assert json.loads(render(rows, ('a',), 'json')) == [{'a': 1}, {'a': 22}]
    assert render([], ('a',)) == '(nothing to report)\n'
