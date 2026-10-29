import io

from lending.cli.main import main


def lend(home, day, *words):
    out, err = io.StringIO(), io.StringIO()
    status = main(['--library', str(home), '--today', day, *words], out, err)
    return status, out.getvalue(), err.getvalue()


def test_checkout_and_return(home):
    assert lend(home, '2026-03-02', 'checkout', 'M1001', '31000001', '31000004') == (
        0, '31000001 due 2026-03-23\n31000004 due 2026-03-09\n', '')
    assert lend(home, '2026-03-12', 'return', '31000004') == (0, '31000004 returned, fine £3.00\n', '')


def test_refusals_print_the_code(home):
    status, out, err = lend(home, '2026-03-02', 'renew', '31000001')
    assert (status, out) == (1, '')
    assert err == 'lend: not_on_loan: 31000001 is not on loan\n'


def test_bad_desk_date(home):
    assert lend(home, 'today', 'status', 'M1001')[2] == 'lend: bad_date: not a date: today\n'


def test_status(home):
    lend(home, '2026-03-02', 'checkout', 'M1001', '31000001')
    status, out, _ = lend(home, '2026-03-02', 'status', 'M1001')
    assert 'on loan: 1\n' in out
    assert out.endswith('can borrow: 19\n')


def test_settings_are_shown_as_written(home):
    out = lend(home, '2026-03-02', 'settings')[1]
    assert 'fine_per_day.DVD = 1.00\n' in out
    assert 'notice_days = 7,21\n' in out


def test_check_finds_nothing_wrong_in_a_fresh_library(home):
    lend(home, '2026-03-02', 'checkout', 'M1001', '31000001')
    assert lend(home, '2026-03-02', 'check') == (0, '0 problems found\n', '')


def test_stocktake(home, tmp_path):
    lend(home, '2026-03-02', 'checkout', 'M1001', '31000001')
    scans = tmp_path / 'scan.txt'
    scans.write_text('31000003\n31000001\n31000002\n31000003\n77\n', encoding='utf-8')
    out = lend(home, '2026-03-02', 'stocktake', 'cen', str(scans), '--format', 'csv')[1]
    assert out.splitlines() == [
        'barcode,title,finding',
        '31000002,The Hobbit,belongs to another branch',
        '31000004,Planet Earth,missing',
        '31000005,The Economist,missing',
        '77,,not in the catalogue',
        '31000001,The Hobbit,scanned but on loan',
    ]


def test_backup_and_restore(home, tmp_path):
    lend(home, '2026-03-02', 'checkout', 'M1001', '31000001')
    assert lend(home, '2026-03-02', 'backup', str(tmp_path / 'saved'))[1] == 'lending-2026-03-02.zip: 3 files\n'
    (home / 'loans.ledger').unlink()
    lend(home, '2026-03-03', 'restore', str(tmp_path / 'saved' / 'lending-2026-03-02.zip'))
    assert '31000001' in lend(home, '2026-03-03', 'loans', 'M1001')[1]
