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


def test_lend_renew_and_take_back(tmp_path):
    home = make_library(tmp_path / 'lib', BOOKS[:3] + DVDS)
    assert lend(home, '2026-03-02', 'checkout', 'M1001', '31000001', '31000901') == (
        0, '31000001 due 2026-03-23\n31000901 due 2026-03-09\n', '')
    assert lend(home, '2026-03-05', 'renew', '31000901') == (0, '31000901 due 2026-03-12\n', '')
    assert lend(home, '2026-03-10', 'return', '31000001') == (0, '31000001 returned\n', '')
    assert lend(home, '2026-03-10', 'checkout', 'M1002', '31000901') == (
        1, '', 'lend: on_loan: 31000901 is already on loan\n')


def can_borrow(home, day, card):
    status, out, _ = lend(home, day, 'status', card)
    assert status == 0
    [line] = [line for line in out.splitlines() if line.startswith('can borrow: ')]
    return int(line.split(': ')[1])


def test_status_says_how_many_more_the_desk_will_lend(tmp_path):
    home = make_library(tmp_path / 'lib', BOOKS + MAGAZINES)
    assert lend(home, '2026-03-02', 'checkout', 'M1001', '31000801', '31000001')[0] == 0
    promised = can_borrow(home, '2026-03-02', 'M1001')
    lent = 0
    for n in range(2, 25):
        status, _, err = lend(home, '2026-03-02', 'checkout', 'M1001', f'3100{n:04d}')
        if status != 0:
            assert err.startswith('lend: loan_limit: ')
            break
        lent += 1
    assert lent == promised
    assert can_borrow(home, '2026-03-02', 'M1001') == 0


def test_renewable_column_matches_what_the_desk_allows(tmp_path):
    home = make_library(tmp_path / 'lib', BOOKS[:3] + DVDS)
    assert lend(home, '2026-03-02', 'checkout', 'M1001', '31000001', '31000002', '31000901')[0] == 0
    assert lend(home, '2026-03-03', 'renew', '31000901')[0] == 0
    assert lend(home, '2026-03-04', 'renew', '31000901')[0] == 0
    assert lend(home, '2026-03-05', 'hold', 'M1002', 'T0001')[0] == 0
    status, out, _ = lend(home, '2026-03-06', 'loans', 'M1001', '--format', 'json')
    assert status == 0
    rows = {row['barcode']: row['renewable'] for row in json.loads(out)}
    assert set(rows) == {'31000001', '31000002', '31000901'}
    for barcode, renewable in sorted(rows.items()):
        status, _, _ = lend(home, '2026-03-06', 'renew', barcode)
        assert (status == 0) == (renewable == 'yes'), barcode


def test_activity_counts_desk_transactions(tmp_path):
    home = make_library(tmp_path / 'lib', BOOKS[:3])
    assert lend(home, '2026-03-02', 'checkout', 'M1001', '31000001', '31000002')[0] == 0
    assert lend(home, '2026-03-10', 'renew', '31000002')[0] == 0
    assert lend(home, '2026-03-20', 'return', '31000002')[0] == 0
    assert lend(home, '2026-03-30', 'return', '31000001')[0] == 0
    assert lend(home, '2026-03-30', 'pay', 'M1001', '1.00')[0] == 0
    status, out, _ = lend(home, '2026-03-31', 'activity', '--format', 'json')
    assert status == 0
    [row] = json.loads(out)
    assert (row['month'], row['issues'], row['renewals'], row['returns'], row['payments']) == (
        '2026-03', 2, 1, 2, 1)


def test_an_export_can_be_imported_into_another_library(tmp_path):
    source = make_library(tmp_path / 'a', BOOKS[:1])
    target = make_library(tmp_path / 'b', BOOKS[:1], members=[])
    assert lend(source, '2026-03-02', 'export', str(tmp_path / 'a.csv'))[0] == 0
    assert lend(target, '2026-03-02', 'import', str(tmp_path / 'a.csv')) == (0, 'imported 4 members\n', '')
    assert lend(target, '2026-03-02', 'export', str(tmp_path / 'b.csv'))[0] == 0
    assert (tmp_path / 'b.csv').read_text(encoding='utf-8') == (tmp_path / 'a.csv').read_text(encoding='utf-8')
