import pytest

from stockroom import Inventory, StockError, new_document


def stocked():
    inventory = Inventory(new_document())
    for code in ('A1', 'B2', 'C3'):
        inventory.add_location(code)
    inventory.add_item('BOLT-M6', 'M6 bolt')
    inventory.add_item('NUT-M6', 'M6 nut')
    inventory.receive('BOLT-M6', 11, 'A1')
    inventory.transfer('BOLT-M6', 5, 'A1', 'B2')
    return inventory


def test_on_hand_is_by_location():
    inventory = stocked()
    assert inventory.on_hand('BOLT-M6') == {'A1': 6, 'B2': 5}
    assert inventory.on_hand('bolt-m6') == {'A1': 6, 'B2': 5}


def test_locations_holding_none_are_left_out():
    inventory = stocked()
    inventory.issue('BOLT-M6', 6, 'A1')
    assert inventory.on_hand('BOLT-M6') == {'B2': 5}
    assert inventory.on_hand('NUT-M6') == {}


def test_unknown_item_is_refused():
    with pytest.raises(StockError) as raised:
        stocked().on_hand('GEAR')
    assert str(raised.value) == 'unknown item: GEAR'
