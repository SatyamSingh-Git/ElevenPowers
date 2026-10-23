from stockroom import Inventory, new_document


def defined():
    inventory = Inventory(new_document())
    inventory.add_location('A1')
    inventory.add_location('B2')
    inventory.add_item('BOLT-M6', 'M6 bolt')
    inventory.add_item('NUT-M6', 'M6 nut')
    return inventory


def test_each_movement_returns_its_seq():
    inventory = defined()
    assert inventory.receive('BOLT-M6', 10, 'A1') == 1
    assert inventory.issue('BOLT-M6', 3, 'A1') == 2
    assert inventory.transfer('BOLT-M6', 2, 'A1', 'B2') == 3
    assert inventory.adjust('BOLT-M6', 'A1', 1) == 4
    assert inventory.receive('NUT-M6', 40, 'B2') == 5


def test_seq_is_an_int_even_for_a_zero_change():
    inventory = defined()
    inventory.receive('NUT-M6', 6, 'B2')
    seq = inventory.adjust('NUT-M6', 'B2', 6)
    assert type(seq) is int and seq == 2


def test_quantities_still_move():
    inventory = defined()
    inventory.receive('BOLT-M6', 10, 'A1')
    inventory.issue('BOLT-M6', 3, 'A1')
    inventory.transfer('BOLT-M6', 2, 'A1', 'B2')
    inventory.adjust('BOLT-M6', 'A1', 1)
    assert (inventory.at('BOLT-M6', 'A1'), inventory.at('BOLT-M6', 'B2')) == (1, 2)
