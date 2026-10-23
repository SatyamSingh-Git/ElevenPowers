import io
import json

from stockroom.cli import main


def cli(path, *argv):
    out, err = io.StringIO(), io.StringIO()
    status = main(['--file', str(path), *argv], stdout=out, stderr=err)
    return status, out.getvalue(), err.getvalue()


def written(tmp_path):
    path = tmp_path / 'stock.json'
    for argv in (('add-location', 'A1'), ('add-location', 'B2'), ('add-item', 'BOLT-M6', 'M6 bolt'),
                 ('receive', 'BOLT-M6', '30', 'A1', '--note', 'PO 7'),
                 ('transfer', 'BOLT-M6', '12', 'A1', 'B2', '--note', 'restock'),
                 ('issue', 'BOLT-M6', '2', 'B2'), ('adjust', 'BOLT-M6', 'A1', '17')):
        status, _, err = cli(path, *argv)
        assert status == 0, err
    return json.loads(path.read_text(encoding='utf-8'))


def test_version_is_3(tmp_path):
    assert written(tmp_path)['version'] == 3


def test_each_line_touches_one_location_with_a_signed_delta(tmp_path):
    lines = written(tmp_path)['movements']
    assert [(m['seq'], m['type'], m['sku'], m['location'], m['delta']) for m in lines] == [
        (1, 'receive', 'BOLT-M6', 'A1', 30),
        (2, 'transfer', 'BOLT-M6', 'A1', -12),
        (2, 'transfer', 'BOLT-M6', 'B2', 12),
        (3, 'issue', 'BOLT-M6', 'B2', -2),
        (4, 'adjust', 'BOLT-M6', 'A1', -1),
    ]
    assert [m['note'] for m in lines[:3]] == ['PO 7', 'restock', 'restock']


def test_old_movement_fields_are_gone(tmp_path):
    for line in written(tmp_path)['movements']:
        assert not {'qty', 'from', 'to'} & set(line)
