"""The `stockroom` command."""
import argparse
from decimal import Decimal
from pathlib import Path
import sys

from . import ledger, reports, store
from ._generated import VERSION
from .inventory import Inventory
from .models import StockError, format_money, normalize_code, normalize_sku


def _add_item(inventory, args, out):
    sku = inventory.add_item(args.sku, args.name, unit=args.unit, reorder_point=args.reorder, cost=args.cost)
    out.write(f'added item {sku}\n')


def _set_reorder(inventory, args, out):
    inventory.set_reorder_point(args.sku, args.point)
    out.write(f'reorder point of {normalize_sku(args.sku)} is now {args.point}\n')


def _add_location(inventory, args, out):
    code = inventory.add_location(args.code, kind=args.kind, description=args.description)
    out.write(f'added location {code}\n')


def _warn_if_low(inventory, sku, out):
    for row in reports.low_stock(inventory):
        if row.sku == sku:
            out.write(f'warning: {sku} is below its reorder point ({row.on_hand} < {row.reorder_point})\n')


def _receive(inventory, args, out):
    now = inventory.receive(args.sku, args.qty, args.location, args.note)
    sku, code = normalize_sku(args.sku), normalize_code(args.location)
    out.write(f'received {args.qty} {sku} at {code} (now {now} there)\n')


def _issue(inventory, args, out):
    left = inventory.issue(args.sku, args.qty, args.location, args.note)
    sku, code = normalize_sku(args.sku), normalize_code(args.location)
    out.write(f'issued {args.qty} {sku} from {code} (now {left} there)\n')
    _warn_if_low(inventory, sku, out)


def _transfer(inventory, args, out):
    now = inventory.transfer(args.sku, args.qty, args.source, args.dest, args.note)
    sku, source, dest = normalize_sku(args.sku), normalize_code(args.source), normalize_code(args.dest)
    out.write(f'moved {args.qty} {sku} from {source} to {dest} (now {now} at {dest})\n')


def _adjust(inventory, args, out):
    change = inventory.adjust(args.sku, args.location, args.count, args.note)
    sku, code = normalize_sku(args.sku), normalize_code(args.location)
    out.write(f'adjusted {sku} at {code} to {args.count} ({change:+d})\n')
    _warn_if_low(inventory, sku, out)


def _show(inventory, args, out):
    sku = normalize_sku(args.sku)
    item = inventory.item(sku)
    out.write(f"{sku}  {item['name']}\n")
    out.write(f"unit: {item['unit']}\n")
    out.write(f"reorder point: {item['reorder_point']}\n")
    out.write(f"unit cost: {format_money(Decimal(item['unit_cost']))}\n")
    for row in reports.stock_levels(inventory, sku):
        out.write(f'  {row.location}  {row.quantity}\n')
    out.write(f'on hand: {inventory.on_hand(sku)}\n')


def _items(inventory, args, out):
    if not inventory.skus():
        out.write('no items\n')
        return
    rows = []
    for sku in inventory.skus():
        item = inventory.item(sku)
        rows.append((sku, item['name'], item['unit'], item['reorder_point'],
                     format_money(Decimal(item['unit_cost']))))
    out.write(reports.table(('SKU', 'NAME', 'UNIT', 'REORDER', 'UNIT COST'), rows, right=(3, 4)) + '\n')


def _locations(inventory, args, out):
    if not inventory.codes():
        out.write('no locations\n')
        return
    rows = []
    for code in inventory.codes():
        location = inventory.location(code)
        held = sum(row.get(code, 0) for row in inventory.doc['stock'].values())
        rows.append((code, location['kind'], held, location['description']))
    out.write(reports.table(('CODE', 'KIND', 'UNITS', 'DESCRIPTION'), rows, right=(2,)) + '\n')


def _stock(inventory, args, out):
    out.write(reports.render_stock(reports.stock_levels(inventory, args.sku)) + '\n')


def _low(inventory, args, out):
    out.write(reports.render_low(reports.low_stock(inventory)) + '\n')


def _value(inventory, args, out):
    out.write(reports.render_value(*reports.valuation(inventory)) + '\n')


def describe(movement):
    kind, qty = movement['type'], movement['qty']
    if kind == 'receive':
        text = f"receive {qty} into {movement['to']}"
    elif kind == 'issue':
        text = f"issue {qty} from {movement['from']}"
    elif kind == 'transfer':
        text = f"transfer {qty} from {movement['from']} to {movement['to']}"
    else:
        text = f"adjust {qty:+d} at {movement['to']}"
    note = f"  ({movement['note']})" if movement['note'] else ''
    return f"#{movement['seq']} {movement['sku']} {text}{note}"


def _history(inventory, args, out):
    movements = inventory.history(args.sku)
    if not movements:
        out.write(f'no movements for {normalize_sku(args.sku)}\n')
    for movement in movements:
        out.write(describe(movement) + '\n')


def _check(inventory, args, out):
    problems = ledger.unknown_references(inventory.doc)
    found = ledger.mismatches(inventory.doc)
    for problem in problems:
        out.write(f'problem: {problem}\n')
    for m in found:
        out.write(f'mismatch: {m.sku} at {m.location}: stock table {m.table}, movements {m.ledger}\n')
    if problems or found:
        return 1
    out.write(f'ok: stock matches {ledger.movement_count(inventory.doc)} movements\n')
    return 0


# name: (handler, writes the file)
COMMANDS = {
    'add-item': (_add_item, True),
    'set-reorder': (_set_reorder, True),
    'add-location': (_add_location, True),
    'receive': (_receive, True),
    'issue': (_issue, True),
    'transfer': (_transfer, True),
    'adjust': (_adjust, True),
    'show': (_show, False),
    'items': (_items, False),
    'locations': (_locations, False),
    'stock': (_stock, False),
    'low': (_low, False),
    'value': (_value, False),
    'history': (_history, False),
    'check': (_check, False),
}


def build_parser():
    parser = argparse.ArgumentParser(prog='stockroom', description='Track stock across locations.')
    parser.add_argument('--file', help=f'data file (default: ${store.FILE_ENV}, else {store.DEFAULT_FILE})')
    commands = parser.add_subparsers(dest='command', required=True)

    command = commands.add_parser('add-item', help='define an item')
    command.add_argument('sku')
    command.add_argument('name')
    command.add_argument('--unit', default='ea')
    command.add_argument('--reorder', default='0', help='reorder point; 0 never reports the item as low')
    command.add_argument('--cost', default='0.00', help='unit cost in dollars, e.g. 2.50')

    command = commands.add_parser('set-reorder', help="change an item's reorder point")
    command.add_argument('sku')
    command.add_argument('point')

    command = commands.add_parser('add-location', help='define a location')
    command.add_argument('code')
    command.add_argument('--kind', default='shelf')
    command.add_argument('--description', default='')

    for name, where in (('receive', 'location'), ('issue', 'location')):
        command = commands.add_parser(name, help=f'{name} stock')
        command.add_argument('sku')
        command.add_argument('qty')
        command.add_argument(where)
        command.add_argument('--note', default='')

    command = commands.add_parser('transfer', help='move stock between locations')
    command.add_argument('sku')
    command.add_argument('qty')
    command.add_argument('source')
    command.add_argument('dest')
    command.add_argument('--note', default='')

    command = commands.add_parser('adjust', help='record a stock count')
    command.add_argument('sku')
    command.add_argument('location')
    command.add_argument('count')
    command.add_argument('--note', default='')

    commands.add_parser('show', help='one item in detail').add_argument('sku')
    commands.add_parser('items', help='list items')
    commands.add_parser('locations', help='list locations and the units each holds')
    commands.add_parser('stock', help='quantities by location').add_argument('sku', nargs='?')
    commands.add_parser('low', help='items below their reorder point')
    commands.add_parser('value', help='value of stock on hand')
    commands.add_parser('history', help="an item's movements").add_argument('sku')
    commands.add_parser('check', help='compare the stock table with the movement log')
    commands.add_parser('version', help='print the release')
    return parser


def main(argv=None, stdout=None, stderr=None, environ=None):
    out, err = stdout or sys.stdout, stderr or sys.stderr
    args = build_parser().parse_args(argv)
    if args.command == 'version':
        out.write(f'stockroom {VERSION}\n')
        return 0
    path = Path(args.file) if args.file else store.default_path(environ)
    handler, writes = COMMANDS[args.command]
    try:
        doc = store.load(path)
        status = handler(Inventory(doc), args, out)
        if writes:
            store.save(path, doc)
    except StockError as exc:
        err.write(f'error: {exc}\n')
        return 1
    return status or 0
