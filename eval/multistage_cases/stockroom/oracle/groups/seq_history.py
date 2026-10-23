import io

from stockroom import Inventory, load, save
from stockroom.cli import main


def cli(path, *argv):
    out = io.StringIO()
    status = main(['--file', str(path), *argv], stdout=out, stderr=io.StringIO())
    return status, out.getvalue()


def test_returned_seq_names_the_movement_in_history(tmp_path):
    path = tmp_path / 'stock.json'
    for argv in (('add-location', 'A1'), ('add-location', 'B2'), ('add-item', 'BOLT-M6', 'M6 bolt'),
                 ('receive', 'BOLT-M6', '40', 'A1'), ('issue', 'BOLT-M6', '1', 'A1'),
                 ('receive', 'BOLT-M6', '2', 'B2')):
        assert cli(path, *argv)[0] == 0
    inventory = Inventory(load(path))
    moved = inventory.transfer('BOLT-M6', 9, 'A1', 'B2', note='restock')
    counted = inventory.adjust('BOLT-M6', 'B2', 30)
    assert (moved, counted) == (4, 5)
    assert {m['seq'] for m in inventory.history('BOLT-M6') if m['type'] == 'transfer'} == {moved}
    assert {m['seq'] for m in inventory.history('BOLT-M6') if m['type'] == 'adjust'} == {counted}
    save(path, inventory.doc)
    lines = cli(path, 'history', 'BOLT-M6')[1].splitlines()
    assert f'#{moved} BOLT-M6 transfer 9 from A1 to B2  (restock)' in lines
    assert f'#{counted} BOLT-M6 adjust +19 at B2' in lines
