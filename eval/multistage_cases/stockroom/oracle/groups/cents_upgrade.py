import io
import json

from stockroom import load
from stockroom.cli import main

VERSION_1 = {
    'version': 1,
    'items': {
        'BOLT-M6': {'name': 'M6 bolt', 'unit': 'ea', 'reorder_point': 20, 'unit_cost': '0.12'},
        'PUMP': {'name': 'Pump', 'unit': 'ea', 'reorder_point': 0, 'unit_cost': '1234.50'},
    },
    'locations': {'A1': {'kind': 'shelf', 'description': 'by the door'}},
    'stock': {'BOLT-M6': {'A1': 15}, 'PUMP': {'A1': 2}},
    'movements': [
        {'seq': 1, 'type': 'receive', 'sku': 'BOLT-M6', 'qty': 15, 'from': None, 'to': 'A1', 'note': ''},
        {'seq': 2, 'type': 'receive', 'sku': 'PUMP', 'qty': 2, 'from': None, 'to': 'A1', 'note': 'PO 9'},
    ],
}


def cli(path, *argv):
    out, err = io.StringIO(), io.StringIO()
    status = main(['--file', str(path), *argv], stdout=out, stderr=err)
    return status, out.getvalue(), err.getvalue()


def old_file(tmp_path):
    path = tmp_path / 'stock.json'
    path.write_text(json.dumps(VERSION_1, indent=2), encoding='utf-8')
    return path


def test_version_1_file_still_reads(tmp_path):
    path = old_file(tmp_path)
    status, out, _ = cli(path, 'value')
    assert status == 0
    lines = [line.split() for line in out.splitlines()]
    assert ['BOLT-M6', '15', '$0.12', '$1.80'] in lines
    assert ['PUMP', '2', '$1,234.50', '$2,469.00'] in lines
    assert lines[-1] == ['TOTAL', '$2,470.80']
    assert 'unit cost: $1,234.50' in cli(path, 'show', 'PUMP')[1].splitlines()
    assert cli(path, 'check') == (0, 'ok: stock matches 2 movements\n', '')


def test_version_1_file_is_rewritten_in_cents(tmp_path):
    path = old_file(tmp_path)
    assert cli(path, 'receive', 'BOLT-M6', '5', 'A1')[0] == 0
    data = json.loads(path.read_text(encoding='utf-8'))
    assert data['version'] >= 2
    assert data['items']['BOLT-M6']['cost_cents'] == 12
    assert data['items']['PUMP']['cost_cents'] == 123450
    assert not [item for item in data['items'].values() if 'unit_cost' in item]
    assert data['items']['PUMP']['name'] == 'Pump'
    assert data['stock'] == {'BOLT-M6': {'A1': 20}, 'PUMP': {'A1': 2}}


def test_library_load_upgrades(tmp_path):
    doc = load(old_file(tmp_path))
    assert doc['items']['BOLT-M6']['cost_cents'] == 12
    assert doc['version'] >= 2
