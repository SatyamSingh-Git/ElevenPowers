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


def test_late_return_is_charged_and_paid_off(tmp_path):
    home = make_library(tmp_path / 'lib', BOOKS + DVDS)
    assert lend(home, '2026-03-02', 'checkout', 'M1001', '31000901')[0] == 0
    assert fine_in(lend(home, '2026-03-14', 'return', '31000901')) == '£5.00'
    assert owes(home, '2026-03-14', 'M1001') == '£5.00'
    assert lend(home, '2026-03-15', 'pay', 'M1001', '2') == (0, 'paid £2.00; balance £3.00\n', '')
    assert owes(home, '2026-03-15', 'M1001') == '£3.00'


def test_overdue_report_quotes_what_a_return_would_cost(tmp_path):
    home = make_library(tmp_path / 'lib', BOOKS + DVDS)
    report_day = date(2026, 5, 1)
    loans = [('31000001', 40, 21), ('31000002', 10, 21), ('31000003', 3, 21), ('31000004', 2, 21),
             ('31000005', 1, 21), ('31000901', 12, 7), ('31000902', 4, 7), ('31000903', 1, 7)]
    for barcode, late, period in sorted(loans, key=lambda loan: -(loan[1] + loan[2])):
        lent = report_day - timedelta(days=late + period)
        assert lend(home, lent.isoformat(), 'checkout', 'M1001', barcode)[0] == 0
    status, out, _ = lend(home, report_day.isoformat(), 'overdue', '--format', 'json')
    assert status == 0
    quoted = {row['barcode']: row['accrued'] for row in json.loads(out)}
    assert {'31000001', '31000002', '31000003', '31000901', '31000902'} <= set(quoted)
    for barcode, _, _ in loans:
        charged = fine_in(lend(home, report_day.isoformat(), 'return', barcode))
        if barcode in quoted:
            assert quoted[barcode] == charged, barcode


def test_member_owing_too_much_cannot_borrow_until_they_pay(tmp_path):
    home = make_library(tmp_path / 'lib', BOOKS + DVDS)
    assert lend(home, '2026-03-02', 'checkout', 'M1001', '31000901')[0] == 0
    assert fine_in(lend(home, '2026-03-15', 'return', '31000901')) == '£6.00'
    status, _, err = lend(home, '2026-03-15', 'checkout', 'M1001', '31000001')
    assert status == 1
    assert err.startswith('lend: member_blocked: ')
    assert lend(home, '2026-03-15', 'pay', 'M1001', '1.50')[0] == 0
    assert lend(home, '2026-03-15', 'checkout', 'M1001', '31000001')[0] == 0
