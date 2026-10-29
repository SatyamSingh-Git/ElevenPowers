import json
from datetime import date

import pytest

from lending import Library

CATALOGUE = {'titles': [
    {'id': 'T0001', 'title': 'The Hobbit', 'author': 'J. R. R. Tolkien', 'material': 'BK',
     'copies': [{'barcode': '31000001', 'branch': 'CEN', 'price': '8.99'},
                {'barcode': '31000002', 'branch': 'RIV', 'price': '8.99'}]},
    {'id': 'T0002', 'title': 'Dune', 'author': 'Frank Herbert', 'material': 'BK',
     'copies': [{'barcode': '31000003', 'branch': 'CEN', 'price': '9.99'}]},
    {'id': 'T0003', 'title': 'Planet Earth', 'author': 'BBC', 'material': 'DVD',
     'copies': [{'barcode': '31000004', 'branch': 'CEN', 'price': '19.99'}]},
    {'id': 'T0004', 'title': 'The Economist', 'author': '', 'material': 'MAG',
     'copies': [{'barcode': '31000005', 'branch': 'CEN', 'price': '6.00'}]},
    {'id': 'T0005', 'title': 'Wolf Hall', 'author': 'Hilary Mantel', 'material': 'AB',
     'copies': [{'barcode': '31000006', 'branch': 'NTH', 'price': '30.00'}]},
]}

MEMBERS = [
    {'card': 'M1001', 'name': 'Ada Lovelace', 'email': 'ada@example.org', 'type': 'adult',
     'born': '1990-04-02', 'joined': '2020-01-15'},
    {'card': 'M1002', 'name': 'Alan Turing', 'email': '', 'type': 'adult',
     'born': '1985-06-23', 'joined': '2021-03-01'},
    {'card': 'C2001', 'name': 'Tom Kitten', 'email': 'kitten@example.org', 'type': 'child',
     'born': '2015-09-10', 'joined': '2022-05-05'},
]

MONDAY = date(2026, 3, 2)


@pytest.fixture
def home(tmp_path):
    (tmp_path / 'catalogue.json').write_text(json.dumps(CATALOGUE), encoding='utf-8')
    (tmp_path / 'members.json').write_text(json.dumps(MEMBERS), encoding='utf-8')
    return tmp_path


@pytest.fixture
def at(home):
    """Open the library in `home` as it stands on a given day."""
    def open_on(day=MONDAY, **options):
        return Library.open(home, day, **options)
    return open_on


@pytest.fixture
def ledger(home):
    """Write a ledger by hand: each line's fields separated by spaces, written with tabs."""
    def write(*lines):
        text = '#lending-ledger v1\n' + ''.join('\t'.join(line.split()) + '\n' for line in lines)
        (home / 'loans.ledger').write_text(text, encoding='utf-8')
    return write
