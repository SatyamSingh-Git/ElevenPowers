import io
import json

from stockroom.cli import main


def cli(path, *argv):
    out, err = io.StringIO(), io.StringIO()
    status = main(['--file', str(path), *argv], stdout=out, stderr=err)
    return status, out.getvalue(), err.getvalue()


def defined(tmp_path):
    path = tmp_path / 'stock.json'
    for argv in (('add-location', 'A1'), ('add-location', 'B2', '--kind', 'bin'),
                 ('add-item', 'BOLT-M6', 'M6 bolt', '--reorder', '5', '--cost', '0.12'),
                 ('add-item', 'NUT-M6', 'M6 nut')):
        assert cli(path, *argv)[0] == 0
    return path


def test_movement_messages(tmp_path):
    path = defined(tmp_path)
    assert cli(path, 'receive', 'bolt-m6', '50', 'a1') == (0, 'received 50 BOLT-M6 at A1 (now 50 there)\n', '')
    assert cli(path, 'receive', 'BOLT-M6', '7', 'A1')[1] == 'received 7 BOLT-M6 at A1 (now 57 there)\n'
    assert cli(path, 'transfer', 'BOLT-M6', '10', 'A1', 'B2')[1] == 'moved 10 BOLT-M6 from A1 to B2 (now 10 at B2)\n'
    assert cli(path, 'transfer', 'BOLT-M6', '3', 'A1', 'B2')[1] == 'moved 3 BOLT-M6 from A1 to B2 (now 13 at B2)\n'
    assert cli(path, 'issue', 'BOLT-M6', '4', 'A1')[1] == 'issued 4 BOLT-M6 from A1 (now 40 there)\n'
    assert cli(path, 'adjust', 'BOLT-M6', 'B2', '11')[1] == 'adjusted BOLT-M6 at B2 to 11 (-2)\n'
    assert cli(path, 'adjust', 'NUT-M6', 'B2', '6')[1] == 'adjusted NUT-M6 at B2 to 6 (+6)\n'


def test_refusal_keeps_the_file(tmp_path):
    path = defined(tmp_path)
    cli(path, 'receive', 'BOLT-M6', '2', 'A1')
    before = path.read_bytes()
    assert cli(path, 'issue', 'BOLT-M6', '3', 'A1') == (
        1, '', 'error: insufficient stock: BOLT-M6 at A1 has 2, needs 3\n')
    assert cli(path, 'transfer', 'BOLT-M6', '3', 'A1', 'B2')[0] == 1
    assert path.read_bytes() == before


def busy(path):
    for argv in (('receive', 'BOLT-M6', '50', 'A1', '--note', 'PO 7'),
                 ('transfer', 'BOLT-M6', '20', 'A1', 'B2'),
                 ('issue', 'BOLT-M6', '5', 'B2', '--note', 'job 12'),
                 ('adjust', 'BOLT-M6', 'A1', '28'),
                 ('receive', 'NUT-M6', '9', 'B2'),
                 ('transfer', 'NUT-M6', '9', 'B2', 'A1')):
        status, _, err = cli(path, *argv)
        assert status == 0, err


def test_history(tmp_path):
    path = defined(tmp_path)
    busy(path)
    assert cli(path, 'history', 'BOLT-M6')[1].splitlines() == [
        '#1 BOLT-M6 receive 50 into A1  (PO 7)',
        '#2 BOLT-M6 transfer 20 from A1 to B2',
        '#3 BOLT-M6 issue 5 from B2  (job 12)',
        '#4 BOLT-M6 adjust -2 at A1',
    ]
    assert cli(path, 'history', 'nut-m6')[1].splitlines() == [
        '#5 NUT-M6 receive 9 into B2',
        '#6 NUT-M6 transfer 9 from B2 to A1',
    ]


def test_check_passes_on_a_consistent_file(tmp_path):
    path = defined(tmp_path)
    busy(path)
    assert cli(path, 'check') == (0, 'ok: stock matches 6 movements\n', '')
    assert cli(path, 'stock')[1].split()[3:] == [
        'BOLT-M6', 'A1', '28', 'BOLT-M6', 'B2', '15', 'NUT-M6', 'A1', '9']


def test_check_catches_a_hand_edited_stock_table(tmp_path):
    path = defined(tmp_path)
    busy(path)
    data = json.loads(path.read_text(encoding='utf-8'))
    data['stock']['BOLT-M6']['B2'] = 99
    data['stock']['NUT-M6'] = {'A1': 9, 'B2': 1}
    path.write_text(json.dumps(data), encoding='utf-8')
    status, out, _ = cli(path, 'check')
    assert status == 1
    assert out.splitlines() == ['mismatch: BOLT-M6 at B2: stock table 99, movements 15',
                                'mismatch: NUT-M6 at B2: stock table 1, movements 0']
