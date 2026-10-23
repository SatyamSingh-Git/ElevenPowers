import io
import json

from stockroom.cli import main

VERSION_2 = {
    'version': 2,
    'items': {'BOLT-M6': {'name': 'M6 bolt', 'unit': 'ea', 'reorder_point': 0, 'cost_cents': 12}},
    'locations': {'A1': {'kind': 'shelf', 'description': ''}, 'B2': {'kind': 'bin', 'description': ''}},
    'stock': {'BOLT-M6': {'A1': 17, 'B2': 10}},
    'movements': [
        {'seq': 1, 'type': 'receive', 'sku': 'BOLT-M6', 'qty': 30, 'from': None, 'to': 'A1', 'note': 'PO 7'},
        {'seq': 2, 'type': 'transfer', 'sku': 'BOLT-M6', 'qty': 12, 'from': 'A1', 'to': 'B2', 'note': ''},
        {'seq': 3, 'type': 'issue', 'sku': 'BOLT-M6', 'qty': 2, 'from': 'B2', 'to': None, 'note': ''},
        {'seq': 4, 'type': 'adjust', 'sku': 'BOLT-M6', 'qty': -1, 'from': None, 'to': 'A1', 'note': 'count'},
    ],
}


def cli(path, *argv):
    out, err = io.StringIO(), io.StringIO()
    status = main(['--file', str(path), *argv], stdout=out, stderr=err)
    return status, out.getvalue(), err.getvalue()


def old_file(tmp_path):
    path = tmp_path / 'stock.json'
    path.write_text(json.dumps(VERSION_2, indent=2), encoding='utf-8')
    return path


def test_version_2_file_reads_as_before(tmp_path):
    path = old_file(tmp_path)
    assert cli(path, 'history', 'BOLT-M6')[1].splitlines() == [
        '#1 BOLT-M6 receive 30 into A1  (PO 7)',
        '#2 BOLT-M6 transfer 12 from A1 to B2',
        '#3 BOLT-M6 issue 2 from B2',
        '#4 BOLT-M6 adjust -1 at A1  (count)',
    ]
    assert cli(path, 'check') == (0, 'ok: stock matches 4 movements\n', '')


def test_version_2_file_is_rewritten_as_lines(tmp_path):
    path = old_file(tmp_path)
    assert cli(path, 'receive', 'BOLT-M6', '3', 'B2')[0] == 0
    data = json.loads(path.read_text(encoding='utf-8'))
    assert data['version'] == 3
    lines = data['movements']
    assert [(m['seq'], m['type'], m['location'], m['delta']) for m in lines] == [
        (1, 'receive', 'A1', 30),
        (2, 'transfer', 'A1', -12),
        (2, 'transfer', 'B2', 12),
        (3, 'issue', 'B2', -2),
        (4, 'adjust', 'A1', -1),
        (5, 'receive', 'B2', 3),
    ]
    assert (lines[0]['note'], lines[4]['note']) == ('PO 7', 'count')
    assert cli(path, 'check') == (0, 'ok: stock matches 5 movements\n', '')
