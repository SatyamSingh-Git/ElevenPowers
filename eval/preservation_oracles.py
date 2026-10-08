"""Controller-owned behavioral checks executed outside candidate workspaces."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from core.process import run

QUEUE_CHECKS = '''
class Base(unittest.TestCase):
    def test_duplicates_and_completion(self):
        q=service.Queue(); q.enqueue("x", [1]); q.enqueue("x", [2])
        payload, token=q.claim("x"); self.assertEqual(payload, [1])
        self.assertFalse(q.ack("x", None)); self.assertFalse(q.ack("x", token+1))
        self.assertTrue(q.ack("x", token)); self.assertFalse(q.ack("x", token))
        q.enqueue("x", 99); self.assertIsNone(q.claim("x"))
    def test_unknown_and_independent_items(self):
        q=service.Queue(); self.assertIsNone(q.claim("missing")); self.assertFalse(q.ack("missing", 1))
        q.enqueue("a", 1); q.enqueue("b", 2)
        a=q.claim("a"); b=q.claim("b"); self.assertNotEqual(a[1], b[1])
        self.assertIsNone(q.claim("a")); self.assertTrue(q.ack("b", b[1]))
    def test_unrelated_formatting(self):
        self.assertEqual(formatting.render(13), "13")

class Lease(unittest.TestCase):
    def test_boundary_and_fencing(self):
        q=service.Queue(); q.enqueue("a", 1)
        self.assertTrue("now" in inspect.signature(q.claim).parameters)
        _, old=q.claim("a", now=7, ttl=3); self.assertIsNone(q.claim("a", now=9, ttl=3))
        claimed=q.claim("a", now=10, ttl=3); self.assertIsNotNone(claimed)
        _, new=claimed; self.assertGreater(new, old)
        self.assertFalse(q.ack("a", old)); self.assertTrue(q.ack("a", new))
    def test_invalid_ttl_preserves_live_claim(self):
        q=service.Queue(); q.enqueue("a", 1)
        self.assertTrue("ttl" in inspect.signature(q.claim).parameters)
        _, token=q.claim("a", now=0, ttl=2)
        for ttl in (0,-1):
            with self.assertRaises(ValueError): q.claim("a", now=100, ttl=ttl)
        self.assertTrue(q.ack("a", token))
    def test_permanent_and_repeated_expiry(self):
        q=service.Queue(); q.enqueue("a", 1); q.enqueue("b", 2)
        self.assertTrue("now" in inspect.signature(q.claim).parameters)
        q.claim("b"); self.assertIsNone(q.claim("b", now=999, ttl=1))
        tokens=[]
        for i in range(5):
            claimed=q.claim("a",now=i,ttl=1); self.assertIsNotNone(claimed); tokens.append(claimed[1])
        self.assertEqual(len(set(tokens)), 5)
        self.assertFalse(q.ack("a", tokens[0]))

class Persistence(unittest.TestCase):
    def test_restart_token_and_deadline(self):
        q=service.Queue(); q.enqueue("a", {"p":[2]}); q.enqueue("done", 0)
        self.assertTrue(callable(getattr(q,"dumps",None))); self.assertTrue(callable(getattr(q,"loads",None)))
        q.ack("done",q.claim("done")[1]); _,old=q.claim("a", now=8, ttl=2)
        r=q.loads(snapshot(self,q)); self.assertIsNone(r.claim("a", now=9, ttl=2))
        payload,new=r.claim("a", now=10, ttl=2); self.assertEqual(payload,{"p":[2]}); self.assertGreater(new,old)
        self.assertFalse(r.ack("a",old)); self.assertTrue(r.ack("a",new)); self.assertIsNone(r.claim("done"))
        r.enqueue("b",0); self.assertGreater(r.claim("b")[1],new)
    def test_snapshot_independence(self):
        q=service.Queue(); q.enqueue("a", [1]); self.assertTrue(callable(getattr(q,"dumps",None)))
        r=q.loads(snapshot(self,q)); payload,token=r.claim("a"); self.assertIsInstance(payload,list); payload.append(2)
        self.assertTrue(r.ack("a",token)); original=q.claim("a")
        self.assertIsNotNone(original); self.assertEqual(original[0],[1])
'''

INVENTORY_CHECKS = '''
class Base(unittest.TestCase):
    def test_idempotence_conflict_and_no_oversell(self):
        s=service.Inventory({"a":5,"b":2}); self.assertTrue(s.reserve("x","a",3))
        self.assertTrue(s.reserve("x","a",3)); self.assertFalse(s.reserve("x","b",3))
        self.assertFalse(s.reserve("x","a",2)); self.assertFalse(s.reserve("y","a",3))
        self.assertEqual(s.available("a"),2); self.assertEqual(s.available("b"),2)
    def test_release_and_invalid_quantity(self):
        s=service.Inventory({"a":3}); s.reserve("x","a",2)
        for qty in (0,-1):
            with self.assertRaises(ValueError): s.reserve("z","a",qty)
        self.assertTrue(s.release("x")); self.assertFalse(s.release("x"))
        self.assertEqual(s.available("a"),3); self.assertEqual(s.available("missing"),0)
    def test_unrelated_formatting(self):
        self.assertEqual(formatting.render(13),"13")

class Expiry(unittest.TestCase):
    def test_boundary_and_live_retry(self):
        s=service.Inventory({"a":5}); self.assertTrue("ttl" in inspect.signature(s.reserve).parameters)
        self.assertTrue(s.reserve("x","a",3,now=7,ttl=3))
        self.assertTrue(s.reserve("x","a",3,now=9,ttl=20))
        self.assertEqual(s.available("a",now=9),2); self.assertEqual(s.available("a",now=10),5)
        self.assertTrue(s.reserve("x","a",4,now=10,ttl=2))
        direct=service.Inventory({"a":1}); direct.reserve("old","a",1,now=0,ttl=1)
        self.assertTrue(direct.reserve("new","a",1,now=1,ttl=1))
    def test_invalid_request_does_not_expire(self):
        s=service.Inventory({"a":3}); self.assertTrue("ttl" in inspect.signature(s.reserve).parameters)
        s.reserve("x","a",2,now=0,ttl=1)
        with self.assertRaises(ValueError): s.reserve("y","a",1,now=10,ttl=0)
        self.assertEqual(s.available("a"),1)
    def test_permanent_sku_and_repeat_expiry(self):
        s=service.Inventory({"a":3,"b":4}); self.assertTrue(callable(getattr(s,"expire",None)))
        s.reserve("x","a",2); s.reserve("y","b",3,now=0,ttl=1)
        s.expire(1); s.expire(100)
        self.assertEqual(s.available("a"),1); self.assertEqual(s.available("b"),4)

class Persistence(unittest.TestCase):
    def test_restart_retry_deadline_and_release_once(self):
        s=service.Inventory({"a":5,"b":3}); self.assertTrue(callable(getattr(s,"dumps",None)))
        s.reserve("x","a",3,now=7,ttl=3); s.reserve("p","b",2)
        r=s.loads(snapshot(self,s)); self.assertEqual(r.available("a"),2)
        self.assertTrue(r.reserve("x","a",3,now=9,ttl=100)); self.assertFalse(r.reserve("x","b",3,now=9))
        self.assertEqual(r.available("a",now=10),5); r.expire(100)
        self.assertEqual(r.available("a"),5); self.assertEqual(r.available("b"),1)
    def test_snapshot_independence(self):
        s=service.Inventory({"a":3}); s.reserve("x","a",2)
        self.assertTrue(callable(getattr(s,"dumps",None))); r=s.loads(snapshot(self,s))
        r.release("x"); self.assertEqual(s.available("a"),1); self.assertEqual(r.available("a"),3)
'''

PREFIX = '''import inspect, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import service, formatting
def snapshot(test,value):
    text=value.dumps(); test.assertIsInstance(text,str)
    try: json.loads(text)
    except (ValueError,TypeError): test.fail("snapshot must be valid JSON")
    return text
'''
SUFFIX = '''
class Results(unittest.TestResult):
    def __init__(self): super().__init__(); self.rows=[]
    def addSuccess(self,test): super().addSuccess(test); self.rows.append({"id":test.id(),"state":"passed"})
    def addFailure(self,test,err): super().addFailure(test,err); self.rows.append({"id":test.id(),"state":"failed"})
    def addError(self,test,err): super().addError(test,err); self.rows.append({"id":test.id(),"state":"error"})
suite=unittest.TestSuite()
for cls in CLASSES[:STAGE+1]: suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
result=Results(); suite.run(result)
print(json.dumps(result.rows))
'''


def oracle(value, stage):
    if value['id'] not in ('queue', 'inventory') or type(stage) is not int or not 0 <= stage <= 2:
        raise ValueError('invalid oracle case or stage')
    checks = QUEUE_CHECKS if value['id'] == 'queue' else INVENTORY_CHECKS
    middle = 'Lease' if value['id'] == 'queue' else 'Expiry'
    return PREFIX + checks + f'\nCLASSES=[Base,{middle},Persistence]\nSTAGE={stage}\n' + SUFFIX


def grade(value, stage, candidate, *, seconds=15):
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 0 < seconds <= 30:
        raise ValueError('invalid grading budget')
    source = oracle(value, stage)
    result = {'state': 'incomplete', 'checks': [], 'passed': 0, 'failed': 0,
              'oracle_sha256': hashlib.sha256(source.encode()).hexdigest(), 'source_sha256': {}, 'elapsed_ms': 0}
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix='ep-preserve-') as folder:
            root = Path(folder)
            for name in value['production']:
                path = Path(candidate) / name
                if path.is_symlink() or not path.is_file() or path.stat().st_size > 256 * 1024:
                    return result
                data = path.read_bytes()
                result['source_sha256'][name] = hashlib.sha256(data).hexdigest()
                (root / name).write_bytes(data)
            (root / '_oracle.py').write_text(source, encoding='utf-8')
            done = run([sys.executable, '-I', '-B', str(root / '_oracle.py')], cwd=root,
                       shell=False, timeout=seconds)
            rows = json.loads(done.stdout)
            count = (3, 6, 8)[stage]
            if (done.returncode != 0 or not isinstance(rows, list) or len(rows) != count
                    or len({r['id'] for r in rows}) != count
                    or any(r['state'] not in ('passed', 'failed', 'error') for r in rows)):
                return result
            result['checks'] = rows
            if not any(r['state'] == 'error' for r in rows):
                result.update(state='graded', passed=sum(r['state'] == 'passed' for r in rows),
                              failed=sum(r['state'] == 'failed' for r in rows))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        pass
    finally:
        result['elapsed_ms'] = round((time.monotonic() - started) * 1000, 3)
    return result
