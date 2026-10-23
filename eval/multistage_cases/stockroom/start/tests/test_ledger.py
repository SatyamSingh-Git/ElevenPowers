import pytest

from stockroom import StockError
from stockroom.ledger import mismatches, replay, unknown_references


def test_replay_matches_the_stock_table(inventory):
    inventory.receive('BOLT-M6', 50, 'A1')
    inventory.transfer('BOLT-M6', 20, 'A1', 'B2')
    inventory.issue('BOLT-M6', 5, 'B2')
    inventory.adjust('BOLT-M6', 'A1', 28)
    assert replay(inventory.doc['movements']) == {'BOLT-M6': {'A1': 28, 'B2': 15}}
    assert mismatches(inventory.doc) == []


def test_hand_edited_stock_is_caught(inventory):
    inventory.receive('BOLT-M6', 50, 'A1')
    inventory.doc['stock']['BOLT-M6']['A1'] = 60
    inventory.doc['stock']['NUT-M6'] = {'B2': 1}
    assert [tuple(m) for m in mismatches(inventory.doc)] == [('BOLT-M6', 'A1', 60, 50), ('NUT-M6', 'B2', 1, 0)]


def test_out_of_order_log_is_refused(inventory):
    inventory.receive('BOLT-M6', 5, 'A1')
    inventory.receive('BOLT-M6', 5, 'A1')
    inventory.doc['movements'].reverse()
    with pytest.raises(StockError, match='movement out of order: #1 after #2'):
        replay(inventory.doc['movements'])


def test_unknown_references(inventory):
    inventory.receive('BOLT-M6', 5, 'A1')
    del inventory.doc['locations']['A1']
    assert unknown_references(inventory.doc) == ['#1 names unknown location A1']
