"""Frozen authored staged contracts; never imported by the shipping runtime."""
from copy import deepcopy

QUEUE = '''class Queue:
    def __init__(self):
        self.items = {}
        self.serial = 0

    def enqueue(self, key, payload):
        if key not in self.items:
            self.items[key] = {"payload": payload, "done": False, "token": None}

    def claim(self, key):
        item = self.items.get(key)
        if item is None or item["done"] or item["token"] is not None:
            return None
        self.serial += 1
        item["token"] = self.serial
        return (item["payload"], item["token"])

    def ack(self, key, token):
        item = self.items.get(key)
        if item is None or item["done"] or token is None or item["token"] != token:
            return False
        item["done"] = True
        return True
'''

QUEUE_ONE = '''class Queue:
    def __init__(self):
        self.items = {}
        self.serial = 0

    def enqueue(self, key, payload):
        if key not in self.items:
            self.items[key] = {"payload": payload, "done": False, "token": None, "until": None}

    def claim(self, key, now=0, ttl=None):
        if ttl is not None and ttl <= 0:
            raise ValueError("ttl must be positive")
        item = self.items.get(key)
        if item is None or item["done"]:
            return None
        if item["token"] is not None and (item["until"] is None or now < item["until"]):
            return None
        self.serial += 1
        item.update(token=self.serial, until=None if ttl is None else now + ttl)
        return (item["payload"], item["token"])

    def ack(self, key, token):
        item = self.items.get(key)
        if item is None or item["done"] or token is None or item["token"] != token:
            return False
        item["done"] = True
        return True
'''

QUEUE_TWO = QUEUE_ONE + '''
    def dumps(self):
        import json
        return json.dumps({"items": self.items, "serial": self.serial})

    @classmethod
    def loads(cls, text):
        import json
        value = json.loads(text)
        result = cls()
        result.items = value["items"]
        result.serial = value["serial"]
        return result
'''

INVENTORY = '''class Inventory:
    def __init__(self, stock):
        self.stock = dict(stock)
        self.reservations = {}

    def available(self, sku):
        return self.stock.get(sku, 0) - sum(r["qty"] for r in self.reservations.values() if r["sku"] == sku)

    def reserve(self, key, sku, qty):
        if qty <= 0:
            raise ValueError("qty must be positive")
        if key in self.reservations:
            r = self.reservations[key]
            return r["sku"] == sku and r["qty"] == qty
        if self.available(sku) < qty:
            return False
        self.reservations[key] = {"sku": sku, "qty": qty}
        return True

    def release(self, key):
        return self.reservations.pop(key, None) is not None
'''

INVENTORY_ONE = '''class Inventory:
    def __init__(self, stock):
        self.stock = dict(stock)
        self.reservations = {}

    def expire(self, now):
        for key, row in list(self.reservations.items()):
            if row["until"] is not None and now >= row["until"]:
                del self.reservations[key]

    def available(self, sku, now=None):
        if now is not None:
            self.expire(now)
        return self.stock.get(sku, 0) - sum(r["qty"] for r in self.reservations.values() if r["sku"] == sku)

    def reserve(self, key, sku, qty, now=0, ttl=None):
        if qty <= 0 or (ttl is not None and ttl <= 0):
            raise ValueError("positive qty and ttl required")
        self.expire(now)
        if key in self.reservations:
            row = self.reservations[key]
            return row["sku"] == sku and row["qty"] == qty
        if self.available(sku) < qty:
            return False
        self.reservations[key] = {"sku": sku, "qty": qty, "until": None if ttl is None else now + ttl}
        return True

    def release(self, key):
        return self.reservations.pop(key, None) is not None
'''

INVENTORY_TWO = INVENTORY_ONE + '''
    def dumps(self):
        import json
        return json.dumps({"stock": self.stock, "reservations": self.reservations})

    @classmethod
    def loads(cls, text):
        import json
        value = json.loads(text)
        result = cls(value["stock"])
        result.reservations = value["reservations"]
        return result
'''

PUBLIC_QUEUE = '''import unittest
from service import Queue

class Core(unittest.TestCase):
    def test_duplicate_enqueue(self):
        q = Queue(); q.enqueue("a", {"x": 1}); q.enqueue("a", {"x": 2})
        self.assertEqual(q.claim("a")[0], {"x": 1})

    def test_ack_and_unknown(self):
        q = Queue(); self.assertIsNone(q.claim("unknown")); q.enqueue("a", 3)
        _, token = q.claim("a"); self.assertFalse(q.ack("a", None))
        self.assertTrue(q.ack("a", token)); self.assertFalse(q.ack("a", token))
        self.assertIsNone(q.claim("a"))

    def test_active_claim(self):
        q = Queue(); q.enqueue("a", 3); q.claim("a")
        self.assertIsNone(q.claim("a"))
'''

PUBLIC_INVENTORY = '''import unittest
from service import Inventory

class Core(unittest.TestCase):
    def test_no_oversell(self):
        s = Inventory({"a": 3}); self.assertTrue(s.reserve("x", "a", 2))
        self.assertFalse(s.reserve("y", "a", 2)); self.assertEqual(s.available("a"), 1)

    def test_idempotence_and_conflict(self):
        s = Inventory({"a": 3}); self.assertTrue(s.reserve("x", "a", 2))
        self.assertTrue(s.reserve("x", "a", 2)); self.assertFalse(s.reserve("x", "a", 1))
        self.assertEqual(s.available("a"), 1)

    def test_release(self):
        s = Inventory({"a": 3}); s.reserve("x", "a", 2)
        self.assertTrue(s.release("x")); self.assertFalse(s.release("x"))
        self.assertEqual(s.available("a"), 3)
'''

REQUESTS = {
    'queue': [
        'Extend Queue.claim(key, now=0, ttl=None) with optional leases. A positive ttl expires at now+ttl; a claim can be taken again at the exact expiry boundary. Each claim gets a new globally increasing integer token. Before expiry, and for ttl=None, a live claim cannot be retaken. Old tokens must never acknowledge a newer claim. A current token can acknowledge its lease until reassignment. Reject nonpositive ttl with ValueError without modifying state. Keep old call signatures, duplicate enqueue semantics, unknown-key handling and permanent completion intact.',
        'Add Queue.dumps() -> JSON string and Queue.loads(text) -> independent Queue. Preserve payloads, permanent completion, current lease deadlines, and the globally increasing token counter across round trips. Deadlines are absolute caller-supplied ticks, not wall-clock time. A restored queue must reject a stale token after lease reassignment, continue increasing tokens and retain all earlier core/lease behavior. Mutating a restored instance must not mutate the original. Inputs need only be valid snapshots produced by dumps and payloads are JSON-compatible.'
    ],
    'inventory': [
        'Extend Inventory.reserve(key, sku, qty, now=0, ttl=None) with optional expiry. Add expire(now), and available(sku, now=None) which expires holds first only when now is supplied. A hold with positive ttl expires exactly at now+ttl; ttl=None stays permanent. reserve expires existing holds at its supplied now before allocating. An identical live retry succeeds without extending its deadline or consuming more stock; conflicting retries fail unchanged. Reject nonpositive qty or ttl with ValueError before modifying any state. Preserve no overselling, SKU isolation, release and old signatures.',
        'Add Inventory.dumps() -> JSON string and Inventory.loads(text) -> independent Inventory. Preserve original stock, every live reservation, idempotency identity and absolute expiry deadline. Restored expiry releases each quantity once, identical retries do not extend deadlines, and conflicting retries do not consume stock. Mutating the restored instance must not mutate the original. Retain all earlier core/expiry behavior. Inputs need only be valid snapshots produced by dumps.'
    ]
}


def case(name):
    if name not in REQUESTS:
        raise ValueError('unknown preservation case')
    base, one, two, public = ((QUEUE, QUEUE_ONE, QUEUE_TWO, PUBLIC_QUEUE) if name == 'queue'
                              else (INVENTORY, INVENTORY_ONE, INVENTORY_TWO, PUBLIC_INVENTORY))
    fault_one = one.replace('now < item["until"]', 'now <= item["until"]') if name == 'queue' else one.replace('now >= row["until"]', 'now > row["until"]')
    fault_two = two.replace('result.serial = value["serial"]', 'result.serial = 0') if name == 'queue' else two.replace('result.reservations = value["reservations"]', 'result.reservations = {}')
    return deepcopy({'id': name, 'production': ['service.py', 'formatting.py'],
        'files': {'service.py': base, 'formatting.py': 'def render(value):\n    return str(value)\n',
                  'tests/test_core.py': public,
                  'tests/test_formatting.py': 'import unittest\nfrom formatting import render\n\nclass Formatting(unittest.TestCase):\n    def test_render(self):\n        self.assertEqual(render(42), "42")\n'},
        'requests': REQUESTS[name], 'gold': [one, two], 'fault': [fault_one, fault_two]})
