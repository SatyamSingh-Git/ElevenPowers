import io
import json

from stockroom.cli import main


def cli(path, *argv):
    out, err = io.StringIO(), io.StringIO()
    status = main(['--file', str(path), *argv], stdout=out, stderr=err)
    return status, out.getvalue(), err.getvalue()


def test_capacity_is_stored_on_the_location(tmp_path):
    path = tmp_path / 'stock.json'
    assert cli(path, 'add-location', 'C3', '--kind', 'bin', '--capacity', '50')[:2] == (0, 'added location C3\n')
    assert cli(path, 'add-location', 'A1')[0] == 0
    locations = json.loads(path.read_text(encoding='utf-8'))['locations']
    assert locations['C3']['capacity'] == 50
    assert locations['A1']['capacity'] is None


def test_cli_refuses_a_receive_that_overfills(tmp_path):
    path = tmp_path / 'stock.json'
    for argv in (('add-location', 'C3', '--capacity', '50'), ('add-item', 'BOLT-M6', 'M6 bolt'),
                 ('receive', 'BOLT-M6', '45', 'C3')):
        assert cli(path, *argv)[0] == 0
    before = path.read_bytes()
    assert cli(path, 'receive', 'BOLT-M6', '15', 'C3') == (
        1, '', 'error: location C3 is full: capacity 50, would hold 60\n')
    assert path.read_bytes() == before
    assert cli(path, 'receive', 'BOLT-M6', '5', 'C3')[0] == 0


def test_locations_from_older_files_have_no_limit(tmp_path):
    path = tmp_path / 'stock.json'
    path.write_text(json.dumps({
        'version': 3,
        'items': {'BOLT-M6': {'name': 'M6 bolt', 'unit': 'ea', 'reorder_point': 0, 'cost_cents': 12}},
        'locations': {'A1': {'kind': 'shelf', 'description': ''}},
        'stock': {}, 'movements': [],
    }), encoding='utf-8')
    assert cli(path, 'receive', 'BOLT-M6', '900000', 'A1')[0] == 0
    assert cli(path, 'check') == (0, 'ok: stock matches 1 movements\n', '')
