import pytest

from stockroom import StockError


def test_receive_issue_and_transfer_move_stock(inventory):
    assert inventory.receive('bolt-m6', 100, 'a1') == 100
    assert inventory.issue('BOLT-M6', 30, 'A1') == 70
    assert inventory.transfer('BOLT-M6', 20, 'A1', 'B2') == 20
    assert inventory.at('BOLT-M6', 'A1') == 50
    assert inventory.at('BOLT-M6', 'B2') == 20
    assert inventory.on_hand('BOLT-M6') == 70


def test_emptied_locations_leave_the_stock_table(inventory):
    inventory.receive('BOLT-M6', 5, 'A1')
    inventory.issue('BOLT-M6', 5, 'A1')
    assert inventory.doc['stock'] == {}


def test_adjust_returns_the_change(inventory):
    inventory.receive('NUT-M6', 10, 'A1')
    assert inventory.adjust('NUT-M6', 'A1', 7) == -3
    assert inventory.adjust('NUT-M6', 'A1', 7) == 0
    assert inventory.at('NUT-M6', 'A1') == 7


def test_movements_are_numbered_in_order(inventory):
    inventory.receive('BOLT-M6', 10, 'A1', note='PO 7')
    inventory.transfer('BOLT-M6', 4, 'A1', 'B2')
    history = inventory.history('BOLT-M6')
    assert [m['seq'] for m in history] == [1, 2]
    assert history[0]['note'] == 'PO 7'
    assert history[1]['from'] == 'A1' and history[1]['to'] == 'B2'


def test_refusals(inventory):
    with pytest.raises(StockError, match='unknown item: GEAR'):
        inventory.receive('gear', 1, 'A1')
    with pytest.raises(StockError, match='unknown location: Z9'):
        inventory.receive('BOLT-M6', 1, 'z9')
    with pytest.raises(StockError, match='insufficient stock: BOLT-M6 at A1 has 0, needs 1'):
        inventory.issue('BOLT-M6', 1, 'A1')
    with pytest.raises(StockError, match='item already exists: BOLT-M6'):
        inventory.add_item('bolt-m6', 'again')
    assert inventory.doc['movements'] == []


def test_items_keep_their_cost(inventory):
    assert inventory.item('BOLT-M6')['unit_cost'] == '0.12'
