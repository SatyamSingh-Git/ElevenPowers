from decimal import Decimal

from stockroom.reports import low_stock, render_low, render_value, stock_levels, valuation


def test_low_stock_uses_the_total_across_locations(inventory):
    inventory.receive('BOLT-M6', 15, 'A1')
    inventory.receive('BOLT-M6', 4, 'B2')
    [row] = low_stock(inventory)
    assert (row.sku, row.on_hand, row.reorder_point, row.shortfall) == ('BOLT-M6', 19, 20, 1)
    inventory.receive('BOLT-M6', 1, 'B2')
    assert low_stock(inventory) == []
    assert render_low([]) == 'no items are below their reorder point'


def test_zero_reorder_point_never_reports(inventory):
    assert [row.sku for row in low_stock(inventory)] == ['BOLT-M6']


def test_valuation(inventory):
    inventory.receive('BOLT-M6', 100, 'A1')
    inventory.receive('NUT-M6', 30, 'B2')
    rows, total = valuation(inventory)
    assert [(r.sku, r.quantity) for r in rows] == [('BOLT-M6', 100), ('NUT-M6', 30)]
    assert total == Decimal('13.50')
    assert render_value(rows, total).splitlines()[-1].split() == ['TOTAL', '$13.50']


def test_stock_levels(inventory):
    inventory.receive('BOLT-M6', 3, 'B2')
    inventory.receive('BOLT-M6', 2, 'A1')
    assert [tuple(r) for r in stock_levels(inventory, 'bolt-m6')] == [('BOLT-M6', 'A1', 2), ('BOLT-M6', 'B2', 3)]
