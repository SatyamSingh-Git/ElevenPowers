import pytest

from stockroom import Inventory, StockError, new_document


def stocked():
    inventory = Inventory(new_document())
    inventory.add_location('A1')
    inventory.add_location('B2', kind='bin')
    inventory.add_item('BOLT-M6', 'M6 bolt', reorder_point=5)
    inventory.receive('BOLT-M6', 10, 'A1')
    return inventory


def test_transfer_to_the_same_location_is_refused():
    inventory = stocked()
    with pytest.raises(StockError) as raised:
        inventory.transfer('BOLT-M6', 5, 'A1', 'A1')
    assert str(raised.value) == 'cannot transfer within one location: A1'


def test_codes_are_compared_after_normalising():
    inventory = stocked()
    with pytest.raises(StockError) as raised:
        inventory.transfer('bolt-m6', 4, ' a1', 'A1 ')
    assert str(raised.value) == 'cannot transfer within one location: A1'


def test_refused_transfer_changes_nothing():
    inventory = stocked()
    with pytest.raises(StockError):
        inventory.transfer('BOLT-M6', 5, 'A1', 'A1')
    assert inventory.at('BOLT-M6', 'A1') == 10
    assert len(inventory.history('BOLT-M6')) == 1
    inventory.transfer('BOLT-M6', 5, 'A1', 'B2')
    assert (inventory.at('BOLT-M6', 'A1'), inventory.at('BOLT-M6', 'B2')) == (5, 5)
