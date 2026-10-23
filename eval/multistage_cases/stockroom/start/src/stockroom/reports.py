"""Low-stock, valuation and stock-level reports, as rows and as text tables."""
from collections import namedtuple
from decimal import Decimal

from .models import format_money, normalize_sku

LowRow = namedtuple('LowRow', 'sku name on_hand reorder_point shortfall')
ValueRow = namedtuple('ValueRow', 'sku quantity unit_cost value')
StockRow = namedtuple('StockRow', 'sku location quantity')


def low_stock(inventory):
    """Items whose total on hand is below their reorder point. A reorder point of 0 never fires."""
    rows = []
    for sku in inventory.skus():
        item = inventory.item(sku)
        point = item['reorder_point']
        held = inventory.on_hand(sku)
        if point and held < point:
            rows.append(LowRow(sku, item['name'], held, point, point - held))
    return rows


def valuation(inventory):
    """Value of what is held, per item and in total. Items with nothing on hand are left out."""
    rows = []
    for sku in inventory.skus():
        held = inventory.on_hand(sku)
        if held:
            cost = Decimal(inventory.item(sku)['unit_cost'])
            rows.append(ValueRow(sku, held, cost, cost * held))
    return rows, sum((row.value for row in rows), Decimal('0.00'))


def stock_levels(inventory, sku=None):
    if sku:
        inventory.item(sku)
        skus = [normalize_sku(sku)]
    else:
        skus = inventory.skus()
    stock = inventory.doc['stock']
    return [StockRow(each, code, qty) for each in skus for code, qty in sorted(stock.get(each, {}).items())]


def table(headers, rows, right=()):
    """Plain text columns; columns whose index is in `right` are right-aligned."""
    cells = [list(map(str, headers))] + [list(map(str, row)) for row in rows]
    widths = [max(len(line[i]) for line in cells) for i in range(len(headers))]
    lines = []
    for line in cells:
        parts = [cell.rjust(width) if i in right else cell.ljust(width)
                 for i, (cell, width) in enumerate(zip(line, widths))]
        lines.append('  '.join(parts).rstrip())
    return '\n'.join(lines)


def render_low(rows):
    if not rows:
        return 'no items are below their reorder point'
    return table(('SKU', 'NAME', 'ON HAND', 'REORDER', 'SHORT'),
                 [(r.sku, r.name, r.on_hand, r.reorder_point, r.shortfall) for r in rows], right=(2, 3, 4))


def render_value(rows, total):
    body = [(r.sku, r.quantity, format_money(r.unit_cost), format_money(r.value)) for r in rows]
    body.append(('TOTAL', '', '', format_money(total)))
    return table(('SKU', 'QTY', 'UNIT COST', 'VALUE'), body, right=(1, 2, 3))


def render_stock(rows):
    if not rows:
        return 'nothing in stock'
    return table(('SKU', 'LOCATION', 'QTY'), rows, right=(2,))
