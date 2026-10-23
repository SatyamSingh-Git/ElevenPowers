"""Audit a data file: rebuild stock from its movement log and compare with its stock table.

This works on the persisted records rather than through `Inventory`, so it can
catch a stock table that was edited by hand or written by a faulty release.
"""
from collections import defaultdict, namedtuple

from .models import StockError

Mismatch = namedtuple('Mismatch', 'sku location table ledger')


def replay(movements):
    """Stock by item and location as the movement log says it should be."""
    stock = defaultdict(lambda: defaultdict(int))
    last = 0
    for movement in movements:
        seq, kind, sku, qty = movement['seq'], movement['type'], movement['sku'], movement['qty']
        if seq <= last:
            raise StockError(f'movement out of order: #{seq} after #{last}')
        last = seq
        if kind == 'receive':
            stock[sku][movement['to']] += qty
        elif kind == 'issue':
            stock[sku][movement['from']] -= qty
        elif kind == 'transfer':
            stock[sku][movement['from']] -= qty
            stock[sku][movement['to']] += qty
        elif kind == 'adjust':
            stock[sku][movement['to']] += qty
        else:
            raise StockError(f'unknown movement type at #{seq}: {kind}')
    return {sku: {code: qty for code, qty in row.items() if qty}
            for sku, row in stock.items() if any(row.values())}


def mismatches(doc):
    """Every item and location where the stock table and the movement log disagree."""
    rebuilt = replay(doc['movements'])
    table = doc['stock']
    found = []
    for sku in sorted(set(table) | set(rebuilt)):
        held, expected = table.get(sku, {}), rebuilt.get(sku, {})
        for code in sorted(set(held) | set(expected)):
            if held.get(code, 0) != expected.get(code, 0):
                found.append(Mismatch(sku, code, held.get(code, 0), expected.get(code, 0)))
    return found


def movement_count(doc):
    return len(doc['movements'])


def unknown_references(doc):
    """Movements naming an item or location the file does not define."""
    items, locations = doc['items'], doc['locations']
    problems = []
    for movement in doc['movements']:
        if movement['sku'] not in items:
            problems.append(f"#{movement['seq']} names unknown item {movement['sku']}")
        for end in ('from', 'to'):
            code = movement[end]
            if code is not None and code not in locations:
                problems.append(f"#{movement['seq']} names unknown location {code}")
    return problems
