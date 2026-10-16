"""Authored Python case assets; never installed with the plugin."""

BASE = '''class Queue:
    def __init__(self, max_attempts=3):
        self.items = {}; self.serial = 0; self.max_attempts = max_attempts
    def enqueue(self, key, payload):
        if key not in self.items: self.items[key] = {"payload": payload, "done": False, "token": None}
    def claim(self, key, now=0, ttl=10):
        row = self.items.get(key)
        if row is None or row["done"] or row["token"] is not None: return None
        self.serial += 1; row["token"] = self.serial
        return row["payload"], self.serial
    def ack(self, key, token):
        row = self.items.get(key)
        if not row or row["done"] or row["token"] is None or row["token"] != token: return False
        row["done"] = True; return True
'''

REFERENCE = '''import json

class Queue:
    def __init__(self, max_attempts=3):
        if type(max_attempts) is not int or max_attempts < 1: raise ValueError("attempts")
        self.items = {}; self.serial = 0; self.max_attempts = max_attempts; self.seen = {}
    def enqueue(self, key, payload):
        if not isinstance(key, str): raise ValueError("key")
        if key not in self.items:
            self.items[key] = {"payload": payload, "done": False, "token": None,
                               "until": None, "attempts": 0, "dead": False}
    def claim(self, key, now=0, ttl=10):
        if type(now) is not int or now < 0 or type(ttl) is not int or ttl < 1: raise ValueError("clock")
        row = self.items.get(key)
        if not row or row["done"] or row["dead"]: return None
        if row["token"] is not None and (row["until"] is None or now < row["until"]): return None
        if row["attempts"] >= self.max_attempts:
            row["dead"] = True; row["token"] = None; return None
        self.serial += 1; row["token"] = self.serial
        row["until"] = now + ttl; row["attempts"] += 1
        return row["payload"], self.serial
    def ack(self, key, token):
        row = self.items.get(key)
        if not row or row["done"] or row["dead"] or row["token"] is None or row["token"] != token: return False
        row["done"] = True; return True
    def retry(self, key, token):
        row = self.items.get(key)
        if not row or row["done"] or row["dead"] or row["token"] is None or row["token"] != token: return False
        row["token"] = None; row["until"] = None
        row["dead"] = row["attempts"] >= self.max_attempts
        return True
    def dumps(self):
        return json.dumps({"version": 2, "serial": self.serial, "max_attempts": self.max_attempts,
                           "items": self.items, "seen": self.seen}, sort_keys=True)
    @classmethod
    def loads(cls, text):
        try:
            value = json.loads(text)
            if value.get("version") not in (1, 2): raise ValueError("version")
            result = cls(value.get("max_attempts", 3))
            if type(value["serial"]) is not int or value["serial"] < 0: raise ValueError("serial")
            result.serial = value["serial"]; result.items = value["items"]
            if not isinstance(result.items, dict): raise ValueError("items")
            for row in result.items.values():
                if not isinstance(row, dict) or not {"payload", "done", "token"} <= row.keys(): raise ValueError("row")
                row.setdefault("until", None)
                row.setdefault("attempts", 1 if row["token"] is not None else 0); row.setdefault("dead", False)
            result.seen = value.get("seen", {})
            if not isinstance(result.seen, dict): raise ValueError("seen")
            return result
        except (TypeError, KeyError, AttributeError) as error: raise ValueError("snapshot") from error
    def dead(self, key):
        return bool(self.items.get(key, {}).get("dead", False))
    def batch(self, keys, now=0, ttl=10):
        if not isinstance(keys, list) or any(not isinstance(k, str) for k in keys) or len(keys) != len(set(keys)):
            raise ValueError("keys")
        clone = Queue.loads(self.dumps()); result = {}
        for key in keys:
            item = clone.claim(key, now, ttl)
            if item is None: return None
            result[key] = item
        self.__dict__.update(clone.__dict__)
        return result
    def replay(self, events):
        if not isinstance(events, list): raise ValueError("events")
        clone = Queue.loads(self.dumps())
        for event in events:
            try:
                identity = event["event"]; op = event["op"]; args = event["args"]
                if not isinstance(identity, str) or not isinstance(args, list) or op not in ("enqueue", "claim", "ack", "retry"):
                    raise ValueError("event")
                signature = json.dumps([op, args], sort_keys=True)
                if identity in clone.seen:
                    if clone.seen[identity] != signature: raise ValueError("conflicting event")
                    continue
                getattr(clone, op)(*args); clone.seen[identity] = signature
            except (KeyError, TypeError) as error: raise ValueError("event") from error
        self.__dict__.update(clone.__dict__)
'''

REQUESTS = [
    'Add leases and retries: claim(key,now=0,ttl=10) validates integer now>=0 and ttl>0 before mutation. A token is live before now+ttl and retakable exactly at expiry. Tokens globally increase; old tokens cannot ack/retry a reassigned claim. retry(key,token) returns bool and releases a current claim. max_attempts is a positive integer constructor option (default3); at that many claims, retry or another expired claim makes the item permanently dead. Preserve duplicate enqueue payload and completed items.',
    'Add dumps()->JSON with version2 and Queue.loads(text)->independent Queue. Preserve payloads, completion, lease deadlines, serial and attempts/max_attempts across restart. Future tokens must exceed earlier tokens. Reject malformed JSON, nonobject/unsupported version and missing required snapshot fields with ValueError. Input is normally a valid own snapshot; do not use wall-clock time.',
    'Add dead(key)->bool and batch(keys,now=0,ttl=10)->dict mapping each key to its (payload,token), in input order. Claim all keys atomically: if any is unknown/completed/live/dead/unclaimable return None and change nothing, including serial. Reject duplicate/nonstring keys or non-list input with ValueError. Empty batch returns {}. Retain earlier retry and restart behavior.',
    'Add version1 migration: loads accepts {version:1,serial:int,items:{key:{payload,done,token}}}; current token is permanent until ack/retry, attempts are1 when token exists else0, max_attempts defaults3. Add replay(events) atomically applying {event:string,op:enqueue|claim|ack|retry,args:list}. Exact duplicate event IDs are ignored, conflicting payload for an ID raises ValueError unchanged. Persist event identities in version2 dumps across restart. Invalid event/batch raises ValueError without partial mutation.'
]

PUBLIC = '''import unittest
from service import Queue
class Core(unittest.TestCase):
    def test_queue(self):
        q=Queue();q.enqueue("a",{"value":1});q.enqueue("a",{"value":2})
        self.assertEqual(q.claim("a"),({"value":1},1));self.assertIsNone(q.claim("a"))
        self.assertFalse(q.ack("a",9));self.assertTrue(q.ack("a",1));self.assertIsNone(q.claim("a"))
'''
