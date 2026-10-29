from datetime import date

import pytest

from lending.errors import LendingError
from lending.storage.ledger import Entry, Ledger


def test_round_trip(tmp_path):
    ledger = Ledger(tmp_path / 'loans.ledger')
    written = [
        Entry(date(2026, 3, 2), 'checkout', '31000001', 'M1001', date(2026, 3, 23), 0),
        Entry(date(2026, 3, 30), 'return', '31000001', 'M1001', date(2026, 3, 23), 175),
        Entry(date(2026, 3, 30), 'payment', None, 'M1001', None, 175),
    ]
    for entry in written:
        ledger.append(entry)
    assert ledger.entries() == written


def test_file_layout(tmp_path):
    ledger = Ledger(tmp_path / 'loans.ledger')
    ledger.append(Entry(date(2026, 3, 30), 'payment', None, 'M1001', None, 250))
    assert (tmp_path / 'loans.ledger').read_text(encoding='utf-8') == (
        '#lending-ledger v1\n2026-03-30\tpayment\t-\tM1001\t-\t2.50\n')


def test_no_file_means_no_entries(tmp_path):
    assert Ledger(tmp_path / 'loans.ledger').entries() == []


@pytest.mark.parametrize('text, problem', [
    ('something else\n', 'line 1: expected #lending-ledger v1'),
    ('#lending-ledger v1\n2026-03-02\tcheckout\t31000001\n', 'line 2: 3 fields, not 6'),
    ('#lending-ledger v1\n2026-03-02\tborrow\t31000001\tM1001\t-\t0.00\n', 'line 2: unknown event borrow'),
    ('#lending-ledger v1\n2026-03-02\tpayment\t-\tM1001\t-\tfree\n', 'line 2: not an amount of money: free'),
])
def test_damaged_ledger(tmp_path, text, problem):
    (tmp_path / 'loans.ledger').write_text(text, encoding='utf-8')
    with pytest.raises(LendingError) as raised:
        Ledger(tmp_path / 'loans.ledger').entries()
    assert raised.value.code == 'bad_ledger'
    assert raised.value.message == f'loans.ledger {problem}'
