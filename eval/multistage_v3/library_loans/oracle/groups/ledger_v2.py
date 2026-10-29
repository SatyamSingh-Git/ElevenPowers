import io
import json
from datetime import date, timedelta

import pytest

from lending.cli.main import main

MEMBERS = [
    {'card': 'M1001', 'name': 'Ada Lovelace', 'email': 'ada@example.org', 'type': 'adult',
     'born': '1990-04-02', 'joined': '2020-01-15'},
    {'card': 'M1002', 'name': 'Alan Turing', 'email': '', 'type': 'adult',
     'born': '1985-06-23', 'joined': '2021-03-01'},
    {'card': 'M1003', 'name': 'Grace Hopper', 'email': 'grace@example.org', 'type': 'adult',
     'born': '1970-12-09', 'joined': '2019-07-30'},
    {'card': 'C2001', 'name': 'Tom Kitten', 'email': '', 'type': 'child',
     'born': '2015-09-10', 'joined': '2022-05-05'},
]


def title(title_id, name, material, *barcodes, price='8.99'):
    return {'id': title_id, 'title': name, 'author': 'Someone', 'material': material,
            'copies': [{'barcode': barcode, 'branch': 'CEN', 'price': price} for barcode in barcodes]}


BOOKS = [title(f'T{n:04d}', f'Book {n}', 'BK', f'3100{n:04d}') for n in range(1, 25)]
DVDS = [title(f'T09{n:02d}', f'Film {n}', 'DVD', f'310009{n:02d}', price='15.00') for n in range(1, 4)]
MAGAZINES = [title(f'T08{n:02d}', f'Monthly {n}', 'MAG', f'310008{n:02d}', price='4.00') for n in range(1, 4)]


def make_library(folder, titles, members=MEMBERS, ini=None):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'catalogue.json').write_text(json.dumps({'titles': titles}), encoding='utf-8')
    (folder / 'members.json').write_text(json.dumps(members), encoding='utf-8')
    if ini is not None:
        (folder / 'lending.ini').write_text('[lending]\n' + ini, encoding='utf-8')
    return folder


def lend(home, day, *words):
    out, err = io.StringIO(), io.StringIO()
    status = main(['--library', str(home), '--today', day, *words], out, err)
    return status, out.getvalue(), err.getvalue()


def fine_in(result):
    status, out, _ = result
    assert status == 0, result
    return out.split(', fine ')[1].split(';')[0].strip() if ', fine ' in out else '£0.00'


def owes(home, day, card):
    status, out, _ = lend(home, day, 'balance', card)
    assert status == 0
    return out.strip().rsplit(' ', 1)[1]


def test_new_ledgers_start_with_the_v2_header(tmp_path):
    home = make_library(tmp_path / 'lib', BOOKS)
    assert lend(home, '2026-03-02', 'checkout', 'M1001', '31000001')[0] == 0
    assert (home / 'loans.ledger').read_text(encoding='utf-8').splitlines()[0] == '#lending-ledger v2'


def test_v1_ledgers_still_open_with_the_same_balances(tmp_path):
    home = make_library(tmp_path / 'lib', BOOKS)
    (home / 'loans.ledger').write_text(
        '#lending-ledger v1\n'
        '2026-02-01\tcheckout\t31000001\tM1001\t2026-02-22\t0.00\n'
        '2026-03-01\treturn\t31000001\tM1001\t2026-02-22\t1.75\n', encoding='utf-8')
    assert owes(home, '2026-03-02', 'M1001') == '£1.75'
    assert lend(home, '2026-03-02', 'pay', 'M1001', '1.00')[0] == 0
    assert owes(home, '2026-03-02', 'M1001') == '£0.75'
    assert (home / 'loans.ledger').read_text(encoding='utf-8').splitlines()[0] == '#lending-ledger v1'
