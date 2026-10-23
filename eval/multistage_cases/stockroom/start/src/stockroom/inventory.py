"""Items, locations and the movements that change what is held where."""
from .models import (
    StockError, check_kind, check_name, check_unit, normalize_code, normalize_sku,
    parse_count, parse_money, parse_qty, parse_reorder_point,
)


class Inventory:
    """Operations on a loaded data document. The caller saves the document afterwards."""

    def __init__(self, doc):
        self.doc = doc

    # Items and locations

    def add_item(self, sku, name, unit='ea', reorder_point=0, cost='0.00'):
        sku = normalize_sku(sku)
        if sku in self.doc['items']:
            raise StockError(f'item already exists: {sku}')
        self.doc['items'][sku] = {
            'name': check_name(name),
            'unit': check_unit(unit),
            'reorder_point': parse_reorder_point(reorder_point),
            'unit_cost': str(parse_money(cost)),
        }
        return sku

    def set_reorder_point(self, sku, value):
        self.item(sku)['reorder_point'] = parse_reorder_point(value)

    def item(self, sku):
        sku = normalize_sku(sku)
        try:
            return self.doc['items'][sku]
        except KeyError:
            raise StockError(f'unknown item: {sku}') from None

    def skus(self):
        return sorted(self.doc['items'])

    def add_location(self, code, kind='shelf', description=''):
        code = normalize_code(code)
        if code in self.doc['locations']:
            raise StockError(f'location already exists: {code}')
        self.doc['locations'][code] = {'kind': check_kind(kind), 'description': description.strip()}
        return code

    def location(self, code):
        code = normalize_code(code)
        try:
            return self.doc['locations'][code]
        except KeyError:
            raise StockError(f'unknown location: {code}') from None

    def codes(self):
        return sorted(self.doc['locations'])

    # Quantities

    def _sku(self, sku):
        self.item(sku)
        return normalize_sku(sku)

    def _code(self, code):
        self.location(code)
        return normalize_code(code)

    def at(self, sku, location):
        """The quantity of one item held at one location."""
        sku, code = self._sku(sku), self._code(location)
        return self.doc['stock'].get(sku, {}).get(code, 0)

    def on_hand(self, sku):
        """The total quantity of an item across all locations."""
        return sum(self.doc['stock'].get(self._sku(sku), {}).values())

    def _set(self, sku, code, qty):
        row = self.doc['stock'].setdefault(sku, {})
        if qty:
            row[code] = qty
        else:
            row.pop(code, None)
        if not row:
            del self.doc['stock'][sku]

    def _record(self, kind, sku, qty, source, dest, note):
        movements = self.doc['movements']
        seq = movements[-1]['seq'] + 1 if movements else 1
        movements.append({'seq': seq, 'type': kind, 'sku': sku, 'qty': qty,
                          'from': source, 'to': dest, 'note': note.strip()})
        return seq

    def _take(self, sku, code, qty):
        have = self.at(sku, code)
        if have < qty:
            raise StockError(f'insufficient stock: {sku} at {code} has {have}, needs {qty}')
        return have

    # Movements

    def receive(self, sku, qty, location, note=''):
        """Book goods in. Returns the quantity now held at the location."""
        sku, code, qty = self._sku(sku), self._code(location), parse_qty(qty)
        now = self.at(sku, code) + qty
        self._set(sku, code, now)
        self._record('receive', sku, qty, None, code, note)
        return now

    def issue(self, sku, qty, location, note=''):
        """Book goods out. Returns the quantity left at the location."""
        sku, code, qty = self._sku(sku), self._code(location), parse_qty(qty)
        left = self._take(sku, code, qty) - qty
        self._set(sku, code, left)
        self._record('issue', sku, qty, code, None, note)
        return left

    def transfer(self, sku, qty, source, dest, note=''):
        """Move goods between locations. Returns the quantity now held at the destination."""
        sku, qty = self._sku(sku), parse_qty(qty)
        source, dest = self._code(source), self._code(dest)
        have = self._take(sku, source, qty)
        there = self.at(sku, dest)
        self._set(sku, source, have - qty)
        self._set(sku, dest, there + qty)
        self._record('transfer', sku, qty, source, dest, note)
        return there + qty

    def adjust(self, sku, location, counted, note=''):
        """Set the quantity at a location to what a count found. Returns the change applied."""
        sku, code, counted = self._sku(sku), self._code(location), parse_count(counted)
        change = counted - self.at(sku, code)
        self._set(sku, code, counted)
        self._record('adjust', sku, change, None, code, note)
        return change

    def history(self, sku):
        sku = self._sku(sku)
        return [movement for movement in self.doc['movements'] if movement['sku'] == sku]
