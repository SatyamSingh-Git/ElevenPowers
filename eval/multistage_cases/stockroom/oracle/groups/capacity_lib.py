import pytest

from stockroom import Inventory, StockError, new_document


def defined():
    inventory = Inventory(new_document())
    inventory.add_location('A1')
    inventory.add_location('C3', kind='bin', capacity=10)
    inventory.add_item('BOLT-M6', 'M6 bolt')
    inventory.add_item('NUT-M6', 'M6 nut')
    return inventory


def refused(call, *args):
    with pytest.raises(StockError) as raised:
        call(*args)
    return str(raised.value)


def test_receive_beyond_capacity_counts_every_item():
    inventory = defined()
    inventory.receive('BOLT-M6', 6, 'C3')
    inventory.receive('NUT-M6', 4, 'C3')
    assert refused(inventory.receive, 'NUT-M6', 1, 'C3') == 'location C3 is full: capacity 10, would hold 11'
    assert (inventory.at('BOLT-M6', 'C3'), inventory.at('NUT-M6', 'C3')) == (6, 4)
    assert len(inventory.history('NUT-M6')) == 1


def test_transfer_beyond_capacity_is_refused():
    inventory = defined()
    inventory.receive('BOLT-M6', 8, 'C3')
    inventory.receive('BOLT-M6', 5, 'A1')
    assert refused(inventory.transfer, 'BOLT-M6', 5, 'A1', 'C3') == 'location C3 is full: capacity 10, would hold 13'
    assert (inventory.at('BOLT-M6', 'A1'), inventory.at('BOLT-M6', 'C3')) == (5, 8)
    inventory.transfer('BOLT-M6', 2, 'A1', 'C3')
    assert inventory.at('BOLT-M6', 'C3') == 10


def test_filling_exactly_to_capacity_is_allowed():
    inventory = defined()
    inventory.receive('BOLT-M6', 10, 'C3')
    inventory.issue('BOLT-M6', 3, 'C3')
    inventory.receive('NUT-M6', 3, 'C3')
    assert inventory.at('NUT-M6', 'C3') == 3


def test_no_capacity_means_no_limit():
    inventory = defined()
    inventory.receive('BOLT-M6', 1_000_000, 'A1')
    inventory.receive('NUT-M6', 1_000_000, 'A1')
    assert inventory.at('NUT-M6', 'A1') == 1_000_000
