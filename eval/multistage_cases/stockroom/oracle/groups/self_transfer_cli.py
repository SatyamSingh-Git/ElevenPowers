import io

from stockroom.cli import main


def cli(path, *argv):
    out, err = io.StringIO(), io.StringIO()
    status = main(['--file', str(path), *argv], stdout=out, stderr=err)
    return status, out.getvalue(), err.getvalue()


def test_cli_refuses_and_leaves_the_file_alone(tmp_path):
    path = tmp_path / 'stock.json'
    for argv in (('add-location', 'A1'), ('add-location', 'B2'), ('add-item', 'BOLT-M6', 'M6 bolt'),
                 ('receive', 'BOLT-M6', '10', 'A1'), ('transfer', 'BOLT-M6', '3', 'A1', 'B2')):
        assert cli(path, *argv)[0] == 0
    before = path.read_bytes()
    assert cli(path, 'transfer', 'BOLT-M6', '5', 'A1', 'a1') == (
        1, '', 'error: cannot transfer within one location: A1\n')
    assert path.read_bytes() == before
    assert cli(path, 'stock', 'BOLT-M6')[1].split()[3:] == ['BOLT-M6', 'A1', '7', 'BOLT-M6', 'B2', '3']
    assert cli(path, 'check') == (0, 'ok: stock matches 2 movements\n', '')
