import io

from stockroom import Inventory, load
from stockroom.cli import main
from stockroom.reports import low_stock


def cli(path, *argv):
    out, err = io.StringIO(), io.StringIO()
    status = main(['--file', str(path), *argv], stdout=out, stderr=err)
    return status, out.getvalue(), err.getvalue()


def stocked(tmp_path):
    path = tmp_path / 'stock.json'
    for argv in (('add-location', 'A1'), ('add-location', 'B2', '--kind', 'bin'),
                 ('add-item', 'BOLT-M6', 'M6 bolt', '--reorder', '20', '--cost', '0.12'),
                 ('add-item', 'NUT-M6', 'M6 nut', '--cost', '0.05'),
                 ('add-item', 'WASHER', 'Washer', '--reorder', '50', '--cost', '1.25'),
                 ('add-item', 'PUMP', 'Pump', '--unit', 'ea', '--cost', '1234.5'),
                 ('receive', 'BOLT-M6', '12', 'A1'), ('receive', 'BOLT-M6', '3', 'B2'),
                 ('receive', 'NUT-M6', '40', 'B2'), ('receive', 'WASHER', '80', 'A1'),
                 ('issue', 'WASHER', '30', 'A1'), ('receive', 'PUMP', '2', 'B2')):
        status, _, err = cli(path, *argv)
        assert status == 0, err
    return path


def line_for(text, first):
    [line] = [line for line in text.splitlines() if line.split() and line.split()[0] == first]
    return line.split()


def test_low_report_lists_only_items_below_their_point(tmp_path):
    path = stocked(tmp_path)
    status, out, _ = cli(path, 'low')
    assert status == 0
    assert line_for(out, 'BOLT-M6')[-3:] == ['15', '20', '5']
    assert not [line for line in out.splitlines() if line.startswith(('WASHER', 'NUT-M6', 'PUMP'))]


def test_low_stock_rows_from_the_library(tmp_path):
    path = stocked(tmp_path)
    rows = low_stock(Inventory(load(path)))
    assert [(r.sku, r.on_hand, r.reorder_point, r.shortfall) for r in rows] == [('BOLT-M6', 15, 20, 5)]


def test_nothing_low(tmp_path):
    path = stocked(tmp_path)
    cli(path, 'receive', 'BOLT-M6', '5', 'B2')
    assert cli(path, 'low')[1] == 'no items are below their reorder point\n'


def test_value_report(tmp_path):
    path = stocked(tmp_path)
    status, out, _ = cli(path, 'value')
    assert status == 0
    assert line_for(out, 'BOLT-M6') == ['BOLT-M6', '15', '$0.12', '$1.80']
    assert line_for(out, 'NUT-M6') == ['NUT-M6', '40', '$0.05', '$2.00']
    assert line_for(out, 'WASHER') == ['WASHER', '50', '$1.25', '$62.50']
    assert line_for(out, 'PUMP') == ['PUMP', '2', '$1,234.50', '$2,469.00']
    assert line_for(out, 'TOTAL') == ['TOTAL', '$2,535.30']


def test_value_leaves_out_items_with_nothing_on_hand(tmp_path):
    path = stocked(tmp_path)
    cli(path, 'add-item', 'GEAR', 'Gear', '--cost', '9.99')
    cli(path, 'issue', 'PUMP', '2', 'B2')
    out = cli(path, 'value')[1]
    assert not [line for line in out.splitlines() if line.startswith(('GEAR', 'PUMP'))]
    assert line_for(out, 'TOTAL') == ['TOTAL', '$66.30']


def test_show_and_items(tmp_path):
    path = stocked(tmp_path)
    shown = cli(path, 'show', 'bolt-m6')[1].splitlines()
    assert 'unit cost: $0.12' in shown
    assert 'on hand: 15' in shown
    assert line_for(cli(path, 'items')[1], 'PUMP')[-1] == '$1,234.50'


def test_issue_warns_when_below_reorder_point(tmp_path):
    path = stocked(tmp_path)
    out = cli(path, 'issue', 'WASHER', '1', 'A1')[1]
    assert 'warning: WASHER is below its reorder point (49 < 50)' in out
    assert 'warning' not in cli(path, 'issue', 'NUT-M6', '39', 'B2')[1]
