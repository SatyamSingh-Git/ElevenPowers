import io
import json

from stockroom import Inventory, new_document
from stockroom.cli import main


def cli(path, *argv):
    out, err = io.StringIO(), io.StringIO()
    status = main(['--file', str(path), *argv], stdout=out, stderr=err)
    return status, out.getvalue(), err.getvalue()


def test_costs_are_written_as_whole_cents(tmp_path):
    path = tmp_path / 'stock.json'
    assert cli(path, 'add-item', 'BOLT-M6', 'M6 bolt', '--cost', '2.50')[0] == 0
    assert cli(path, 'add-item', 'NUT-M6', 'M6 nut', '--cost', '$0.07')[0] == 0
    assert cli(path, 'add-item', 'PUMP', 'Pump', '--cost', '1234')[0] == 0
    assert cli(path, 'add-item', 'FREE', 'Sample')[0] == 0
    data = json.loads(path.read_text(encoding='utf-8'))
    assert data['version'] >= 2
    costs = {sku: item['cost_cents'] for sku, item in data['items'].items()}
    assert costs == {'BOLT-M6': 250, 'NUT-M6': 7, 'PUMP': 123400, 'FREE': 0}
    assert all(type(cost) is int for cost in costs.values())
    assert not [item for item in data['items'].values() if 'unit_cost' in item]


def test_library_items_carry_cents():
    inventory = Inventory(new_document())
    inventory.add_item('GEAR', 'Gear', cost='19.9')
    assert inventory.item('GEAR')['cost_cents'] == 1990
    assert 'unit_cost' not in inventory.item('GEAR')


def test_dollars_still_go_in_and_come_out(tmp_path):
    path = tmp_path / 'stock.json'
    cli(path, 'add-location', 'A1')
    cli(path, 'add-item', 'GEAR', 'Gear', '--cost', '19.9')
    cli(path, 'receive', 'GEAR', '3', 'A1')
    assert 'unit cost: $19.90' in cli(path, 'show', 'GEAR')[1].splitlines()
    assert cli(path, 'value')[1].splitlines()[-1].split() == ['TOTAL', '$59.70']
    assert cli(path, 'add-item', 'BAD', 'Bad', '--cost', '1.999')[2] == (
        'error: cost must be dollars and cents, like 2.50: 1.999\n')
