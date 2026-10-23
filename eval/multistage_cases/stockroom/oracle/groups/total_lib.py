import io

import pytest

from stockroom import Inventory, StockError, load
from stockroom.cli import main


def built(tmp_path):
    path = tmp_path / 'stock.json'
    for argv in (('add-location', 'A1'), ('add-location', 'B2'), ('add-item', 'BOLT-M6', 'M6 bolt'),
                 ('add-item', 'NUT-M6', 'M6 nut'), ('receive', 'BOLT-M6', '30', 'A1'),
                 ('transfer', 'BOLT-M6', '12', 'A1', 'B2'), ('issue', 'BOLT-M6', '2', 'B2')):
        assert main(['--file', str(path), *argv], stdout=io.StringIO(), stderr=io.StringIO()) == 0
    return Inventory(load(path))


def test_total_sums_every_location(tmp_path):
    inventory = built(tmp_path)
    assert inventory.total('BOLT-M6') == 28
    assert inventory.total('bolt-m6') == 28


def test_total_is_zero_when_nothing_is_held(tmp_path):
    assert built(tmp_path).total('NUT-M6') == 0


def test_total_of_unknown_item_is_refused(tmp_path):
    with pytest.raises(StockError) as raised:
        built(tmp_path).total('GEAR')
    assert str(raised.value) == 'unknown item: GEAR'
