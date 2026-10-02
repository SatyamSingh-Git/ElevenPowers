"""Authored task contracts and references, never copied as answers to an agent.

Borrow Python's sqlite3/asyncio/json primitives; add interacting task contracts.
These small reference implementations validate the evaluator, not the product.
"""

QUEUE_PROMPT = '''Repair app.service.Queue, a durable multi-tenant job queue backed by SQLite.
Preserve public APIs. Queue(path) opens or creates the same durable database.
enqueue(tenant,key,payload) returns True only for a new job, False for an identical
retry even after completion; a different payload for the same tenant/key raises
ValueError without altering durable state. JSON payload/result must be finite
JSON data. Object key order does not distinguish payloads. Tenant/key/worker
are nonempty strings. Reject booleans/nonfinite/negative times, nonpositive
lease durations, and nonpositive/noninteger tokens with ValueError.
claim(tenant,worker,now,lease) atomically leases the oldest eligible job in that
tenant and returns (key,payload,token), or None. Eligible means unfinished and
unclaimed or deadline <= now. Tokens are positive integers increasing on every
claim of that job, including by the same worker. Separate Queue objects and
concurrent workers must never claim one active job twice. lease expiry is exact.
ack(tenant,key,token,now,result) returns True only if that token still owns an
unexpired unfinished lease; it durably commits the result and finishes the job
atomically. Stale, expired, missing and completed acknowledgements return False.
renew(tenant,key,token,now,lease) follows the same ownership rule and returns a
boolean; extend deadline to max(existing deadline, now+lease), never shorten it.
results(tenant) returns only completed key->result entries, pending(tenant) counts
unfinished jobs. Successful calls survive closing/reopening. Invalid calls and
conflicting retries leave existing state unchanged. Handle actual SQLite locking;
do not substitute a process-local dictionary. Tenant isolation applies everywhere.
Use transaction boundaries so competing writers and crashes cannot split a
read-modify-write operation. Preserve all seeded checks. Add regression tests in
tests/test_regression.py as useful. Run python visible.py after your final edit.
'''

QUEUE = '''import json
import math
import sqlite3
from contextlib import contextmanager

def text(value):
    if type(value) is not str or not value:
        raise ValueError('nonempty string required')

def number(value, positive=False):
    if type(value) not in (int,float) or not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError('invalid time')

def packed(value):
    return json.dumps(value, sort_keys=True, separators=(',',':'), allow_nan=False)

class Queue:
    def __init__(self,path):
        self.path=str(path)
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS jobs (tenant TEXT,key TEXT,payload TEXT,token INTEGER DEFAULT 0,deadline REAL,done INTEGER DEFAULT 0,result TEXT,PRIMARY KEY(tenant,key))')

    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=5,isolation_level=None)
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def enqueue(self,tenant,key,payload):
        text(tenant);text(key);value=packed(payload)
        with self.db() as db:
            old=db.execute('SELECT payload FROM jobs WHERE tenant=? AND key=?',(tenant,key)).fetchone()
            if old:
                if old[0]!=value:
                    raise ValueError('conflicting retry')
                return False
            db.execute('INSERT INTO jobs(tenant,key,payload) VALUES(?,?,?)',(tenant,key,value))
            return True

    def claim(self,tenant,worker,now,lease):
        text(tenant);text(worker);number(now);number(lease,True)
        with self.db() as db:
            row=db.execute('SELECT key,payload,token FROM jobs WHERE tenant=? AND done=0 AND (deadline IS NULL OR deadline<=?) ORDER BY rowid LIMIT 1',(tenant,now)).fetchone()
            if not row:
                return None
            key,payload,token=row;token+=1
            db.execute('UPDATE jobs SET token=?,deadline=? WHERE tenant=? AND key=?',(token,now+lease,tenant,key))
            return key,json.loads(payload),token

    def _owned(self,db,tenant,key,token,now):
        text(tenant);text(key);number(now)
        if type(token) is not int or token<=0:
            raise ValueError('invalid token')
        row=db.execute('SELECT deadline,done,token FROM jobs WHERE tenant=? AND key=?',(tenant,key)).fetchone()
        return bool(row and not row[1] and row[2]==token and row[0] is not None and now<row[0])

    def ack(self,tenant,key,token,now,result):
        value=packed(result)
        with self.db() as db:
            if not self._owned(db,tenant,key,token,now):
                return False
            db.execute('UPDATE jobs SET done=1,result=? WHERE tenant=? AND key=?',(value,tenant,key))
            return True

    def renew(self,tenant,key,token,now,lease):
        number(lease,True)
        with self.db() as db:
            if not self._owned(db,tenant,key,token,now):
                return False
            db.execute('UPDATE jobs SET deadline=MAX(deadline,?) WHERE tenant=? AND key=?',(now+lease,tenant,key))
            return True

    def results(self,tenant):
        text(tenant)
        with self.db() as db:
            return {k:json.loads(v) for k,v in db.execute('SELECT key,result FROM jobs WHERE tenant=? AND done=1',(tenant,))}

    def pending(self,tenant):
        text(tenant)
        with self.db() as db:
            return db.execute('SELECT COUNT(*) FROM jobs WHERE tenant=? AND done=0',(tenant,)).fetchone()[0]
'''

CACHE_PROMPT = '''Repair app.service.Cache(fetch,clock,ttl,capacity), an asyncio cache.
fetch(tenant,key) is async; clock() returns an injected monotonic number.
await get(tenant,key) caches any result including None. Keys are tenant-scoped.
Fresh means clock() < completion-time + ttl; expiry at equality is stale.
At most one current fetch per tenant/key/generation; concurrent misses coalesce.
Cancelling one waiter must not cancel shared work or other waiters. Propagate
fetch errors, remove the failed flight, and allow later retry. Never retain a
failed result. Hit order and successful insertion drive LRU eviction; capacity
limits cached values, not in-flight requests. Validate nonempty string tenant/key,
finite positive ttl (not bool), and positive integer capacity (not bool).
invalidate(tenant,key) synchronously removes a value and advances that key's
generation. Callers already waiting may receive their old response, but it must
never repopulate the cache or be joined by new get calls. Old-flight cleanup must
not delete a newer flight. Two invalidations and reverse-order completions must
behave consistently. Different tenants must neither coalesce nor invalidate one
another. TTL starts when fetch completes, not when it was requested.
await close() marks the cache closed, cancels/awaits every outstanding fetch,
clears cached state, and is idempotent. After closing, get and invalidate raise
RuntimeError; waiting gets may propagate CancelledError. Do not swallow caller
cancellation. Use deterministic clock/event schedules in tests rather than
relying on sleep timing. Preserve APIs and seeded tests; add useful regressions
in tests/test_regression.py. Run python visible.py after the final edit.
'''

CACHE = '''import asyncio
import math
from collections import OrderedDict

class Cache:
    def __init__(self,fetch,clock,ttl,capacity):
        if type(ttl) not in (int,float) or not math.isfinite(ttl) or ttl<=0 or type(capacity) is not int or capacity<=0:
            raise ValueError('invalid cache bounds')
        self.fetch,self.clock,self.ttl,self.capacity=fetch,clock,ttl,capacity
        self.values=OrderedDict();self.flights={};self.generations={};self.tasks=set();self.closed=False

    def _key(self,tenant,key):
        if self.closed:
            raise RuntimeError('closed')
        if type(tenant) is not str or not tenant or type(key) is not str or not key:
            raise ValueError('invalid key')
        return tenant,key

    async def get(self,tenant,key):
        k=self._key(tenant,key)
        if k in self.values:
            value,deadline=self.values[k]
            if self.clock()<deadline:
                self.values.move_to_end(k)
                return value
            del self.values[k]
        if k not in self.flights:
            generation=self.generations.get(k,0)
            task=asyncio.create_task(self._load(k,generation))
            self.flights[k]=(generation,task);self.tasks.add(task)
            task.add_done_callback(self._finished)
        return await asyncio.shield(self.flights[k][1])

    def _finished(self,task):
        self.tasks.discard(task)
        if not task.cancelled():
            task.exception()

    async def _load(self,k,generation):
        try:
            value=await self.fetch(*k)
            if not self.closed and self.generations.get(k,0)==generation:
                self.values[k]=(value,self.clock()+self.ttl);self.values.move_to_end(k)
                while len(self.values)>self.capacity:
                    self.values.popitem(last=False)
            return value
        finally:
            current=self.flights.get(k)
            if current and current[1] is asyncio.current_task():
                del self.flights[k]

    def invalidate(self,tenant,key):
        k=self._key(tenant,key)
        self.values.pop(k,None);self.generations[k]=self.generations.get(k,0)+1
        self.flights.pop(k,None)

    async def close(self):
        self.closed=True
        self.values.clear();self.flights.clear()
        tasks=list(self.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
'''

PLANNER_PROMPT = '''Repair app.service.plan(previous,current,changed), an incremental build planner.
Each graph maps nonempty string node -> {'deps': list of nonempty node names,
'stamp': nonempty string}. Every dependency must exist in that same graph.
Reject malformed graphs and cycles anywhere, even outside the impacted subgraph,
with ValueError. Duplicate deps may be deduplicated. changed is a list of nonempty
strings; duplicates are allowed, but each name must appear in either graph.
Never mutate any argument. Detect added/deleted nodes and any changed stamp or
dependency set even when changed is empty; dependency ordering is immaterial.
Compute impact transitively using BOTH old and new reverse-dependency relations.
This matters when a dependency is removed, renamed, or replaced: an old chain
still invalidates surviving consumers. Newly added nodes are always affected.
Return {'rebuild': [surviving impacted nodes in deterministic dependency-first
topological order], 'removed': sorted deleted nodes}. Only schedule impacted
survivors. Dependencies that are unaffected need not be included. Among currently
ready nodes, always choose lexicographically smallest; input dict/list ordering
must not affect output. A rename is deletion plus addition and corresponding
dependency changes. An unchanged disconnected component must not rebuild.
Handle diamonds, deep chains, old-only edges and multiple deleted nodes.
Preserve app.helpers.summarize(result): {'count': len(rebuild),'removed':len(removed)}.
Preserve APIs and seeded checks; add useful regressions in tests/test_regression.py.
Run python visible.py after the final edit.
'''

PLANNER = '''import heapq
from app.helpers import summarize

def graph(value):
    if type(value) is not dict or any(type(k) is not str or not k for k in value):
        raise ValueError('invalid graph')
    normalized={}
    for name,row in value.items():
        if type(row) is not dict or set(row)!={'deps','stamp'} or type(row['stamp']) is not str or not row['stamp'] or type(row['deps']) is not list or any(type(d) is not str or not d or d not in value for d in row['deps']):
            raise ValueError('invalid node')
        normalized[name]=(set(row['deps']),row['stamp'])
    order(normalized,set(normalized))
    return normalized

def order(g,selected):
    degree={n:len(g[n][0]&selected) for n in selected}
    reverse={n:set() for n in selected}
    for n in selected:
        for dependency in g[n][0]&selected:
            reverse[dependency].add(n)
    ready=[n for n,d in degree.items() if not d];heapq.heapify(ready);result=[]
    while ready:
        n=heapq.heappop(ready);result.append(n)
        for dependent in reverse[n]:
            degree[dependent]-=1
            if degree[dependent]==0:
                heapq.heappush(ready,dependent)
    if len(result)!=len(selected):
        raise ValueError('cycle')
    return result

def plan(previous,current,changed):
    old,new=graph(previous),graph(current)
    if type(changed) is not list or any(type(n) is not str or not n or n not in old.keys()|new.keys() for n in changed):
        raise ValueError('invalid changes')
    affected=set(changed)|set(old)^set(new)
    affected.update(n for n in old.keys()&new.keys() if old[n]!=new[n])
    reverse={n:set() for n in old.keys()|new.keys()}
    for g in (old,new):
        for n,(dependencies,stamp) in g.items():
            for d in dependencies:
                reverse[d].add(n)
    pending=list(affected)
    while pending:
        for n in reverse[pending.pop()]:
            if n not in affected:
                affected.add(n);pending.append(n)
    return {'rebuild':order(new,affected&new.keys()),'removed':sorted(old.keys()-new.keys())}
'''

STREAM_PROMPT = '''Repair app.service.Stream, a resumable transactional JSON-lines processor.
Stream(checkpoint=None) starts empty or restores checkpoint(). feed(chunk,final=False)
accepts bytes, returns newly accepted {'id':str,'value':JSON} records in order.
Input is UTF-8 with LF or CRLF line endings; ignore whitespace-only lines.
Each nonblank line is a JSON object with exactly id and value, id a nonempty
string, value arbitrary finite JSON data. Reject duplicate JSON member names and
NaN/Infinity anywhere. Identical IDs with structurally identical values are
idempotent and return no new output; conflicting reuse raises ValueError.
Object member order is immaterial; distinguish bool, integer and float values.
Chunks may split UTF-8 code points, JSON tokens, CRLF, or an entire record.
Only complete lines are parsed before final=True. Final accepts one last record
without newline; incomplete UTF-8/JSON raises ValueError. Never drop a trailing
record. After successful final, feed raises ValueError (including empty feed).
Each feed is atomic: any invalid line, conflict or decoding error rolls back
every change from that chunk, including accepted IDs, byte offset and buffered
bytes. A caller can retry corrected bytes after rejection. After rejection,
checkpoint() must equal its previous value. Previously accepted chunks survive.
checkpoint() is a detached JSON-serializable dict with exactly offset (all
successfully supplied raw bytes), pending (base64 undecoded/unprocessed suffix),
seen (id->typed signature string), and finished (bool). Restore validates the
exact schema, nonnegative integer offset excluding bool, strict base64 pending,
nonempty seen IDs, signature format, pending length <= offset, and finished
with empty pending. Typed signature is canonical JSON of recursive type tags:
None ['none']; bool/int/float/str [type-name,value]; list ['list',[signatures]];
dict ['dict',[[key,signature],...]] sorted by key. Signature is compact JSON
with ensure_ascii=False (literal Unicode, no optional spaces).
Restoring an unfinished multibyte fragment must accept its remaining bytes.
Preserve app.helpers.commit(checkpoint,chunk,sink,final=False): build a Stream,
feed it, call sink(new_records) exactly once, and return the new checkpoint only
if sink succeeds. Do not mutate the caller's checkpoint. A failed sink leaves
the old checkpoint usable for retry with exactly the same new output; arbitrary
external sink effects themselves are the caller's transaction responsibility.
Preserve APIs/seeded checks; add regressions in tests/test_regression.py.
Run python visible.py after your final edit.
'''

STREAM = '''import base64
import copy
import json

def tagged(v):
    if v is None:
        return ['none']
    if type(v) in (bool,int,float,str):
        return [type(v).__name__,v]
    if type(v) is list:
        return ['list',[tagged(x) for x in v]]
    if type(v) is dict:
        return ['dict',[[k,tagged(v[k])] for k in sorted(v)]]
    raise ValueError('invalid JSON')

def signature(v):
    return json.dumps(tagged(v),separators=(',',':'),allow_nan=False,ensure_ascii=False)

def pairs(items):
    result={}
    for k,v in items:
        if k in result:
            raise ValueError('duplicate member')
        result[k]=v
    return result

def invalid(v):
    raise ValueError('nonfinite JSON')

def valid_tag(v):
    if type(v) is not list or not v:
        return False
    if v==['none']:
        return True
    if len(v)!=2:
        return False
    tag,value=v
    if tag in ('bool','int','float','str'):
        return type(value).__name__==tag
    if tag=='list':
        return type(value) is list and all(valid_tag(x) for x in value)
    if tag=='dict':
        return type(value) is list and all(type(p) is list and len(p)==2 and type(p[0]) is str and valid_tag(p[1]) for p in value) and [p[0] for p in value]==sorted(set(p[0] for p in value))
    return False

class Stream:
    def __init__(self,checkpoint=None):
        value=checkpoint if checkpoint is not None else {'offset':0,'pending':'','seen':{},'finished':False}
        try:
            if type(value) is not dict or set(value)!={'offset','pending','seen','finished'} or type(value['offset']) is not int or value['offset']<0 or type(value['pending']) is not str or type(value['finished']) is not bool or type(value['seen']) is not dict:
                raise ValueError('invalid checkpoint')
            pending=base64.b64decode(value['pending'],validate=True)
            if len(pending)>value['offset'] or (value['finished'] and pending):
                raise ValueError('invalid pending bytes')
            for k,s in value['seen'].items():
                if type(k) is not str or not k or type(s) is not str or not valid_tag(json.loads(s,parse_constant=invalid)):
                    raise ValueError('invalid signature')
                if json.dumps(json.loads(s),separators=(',',':'),allow_nan=False,ensure_ascii=False)!=s:
                    raise ValueError('noncanonical signature')
            self.state=copy.deepcopy(value)
        except (TypeError,KeyError,ValueError) as error:
            raise ValueError('invalid checkpoint') from error

    def checkpoint(self):
        return copy.deepcopy(self.state)

    def feed(self,chunk,final=False):
        if type(chunk) is not bytes or type(final) is not bool or self.state['finished']:
            raise ValueError('invalid feed')
        work=self.checkpoint();raw=base64.b64decode(work['pending'])+chunk
        lines=raw.split(b'\\n');pending=lines.pop()
        if final:
            lines.append(pending);pending=b''
        result=[]
        try:
            for line in lines:
                decoded=line.decode('utf-8')
                if not decoded.strip():
                    continue
                record=json.loads(decoded,object_pairs_hook=pairs,parse_constant=invalid)
                if type(record) is not dict or set(record)!={'id','value'} or type(record['id']) is not str or not record['id']:
                    raise ValueError('invalid record')
                s=signature(record['value']);key=record['id']
                if key in work['seen']:
                    if work['seen'][key]!=s:
                        raise ValueError('conflicting ID')
                else:
                    work['seen'][key]=s;result.append(record)
            # Reject definite invalid UTF-8 promptly while admitting partial tails.
            import codecs
            codecs.getincrementaldecoder('utf-8')().decode(pending,final=False)
        except (UnicodeError,ValueError,TypeError) as error:
            raise ValueError('invalid input') from error
        work.update(offset=work['offset']+len(chunk),pending=base64.b64encode(pending).decode(),finished=final)
        self.state=work
        return result
'''

GOLD = {'lease-queue':QUEUE,'async-cache':CACHE,'build-planner':PLANNER,'resumable-stream':STREAM}
PROMPTS = {'lease-queue':QUEUE_PROMPT,'async-cache':CACHE_PROMPT,'build-planner':PLANNER_PROMPT,'resumable-stream':STREAM_PROMPT}
HELPERS = {
    'lease-queue':'def summarize(queue,tenant):\n    return {"pending":queue.pending(tenant),"results":queue.results(tenant)}\n',
    'async-cache':'async def fetch_pair(cache,tenant,key):\n    import asyncio\n    return await asyncio.gather(cache.get(tenant,key),cache.get(tenant,key))\n',
    'build-planner':'def summarize(result):\n    return {"count":len(result["rebuild"]),"removed":len(result["removed"])}\n',
    'resumable-stream':'def commit(checkpoint,chunk,sink,final=False):\n    from app.service import Stream\n    stream=Stream(checkpoint)\n    records=stream.feed(chunk,final)\n    sink(records)\n    return stream.checkpoint()\n',
}
# Plausible faults also form the free adversarial controls. Gold is not exposed.
REPLACEMENTS = {
    'lease-queue':[
        ('row[2]==token and row[0] is not None and now<row[0]', 'row[0] is not None'),
        ('MAX(deadline,?)','?'),
        ("if old[0]!=value:","if False:"),
        ('deadline<=?','deadline<?'),
    ],
    'async-cache':[
        ('await asyncio.shield(self.flights[k][1])','await self.flights[k][1]'),
        ('not self.closed and self.generations.get(k,0)==generation','not self.closed'),
        ('self.flights.pop(k,None)','pass'),
        ('self.clock()<deadline','self.clock()<=deadline'),
    ],
    'build-planner':[
        ('affected.add(n);pending.append(n)','affected.add(n)'),
        ('order(normalized,set(normalized))','pass'),
        ('if old[n]!=new[n]','if old[n][1]!=new[n][1]'),
        ('n=heapq.heappop(ready)','n=ready.pop()'),
    ],
    'resumable-stream':[
        ("work=self.checkpoint();raw=", "work=self.state;raw="),
        ("lines.append(pending);pending=b''", "pending=b''"),
        ("if work['seen'][key]!=s:", 'if False:'),
        ('self.state=work','work["offset"]-=len(chunk);self.state=work'),
    ],
}

VISIBLE = {
 'lease-queue':'''import tempfile
from app.service import Queue
class Seed(unittest.TestCase):
    def test_transfer_lifecycle(self):
        with tempfile.TemporaryDirectory() as d:
            q=Queue(d+'/queue.db');self.assertTrue(q.enqueue('t','a',{'x':1}))
            item=q.claim('t','w',0,10);self.assertEqual(item,('a',{'x':1},1))
            self.assertTrue(q.ack('t','a',1,1,'done'));self.assertEqual(q.results('t'),{'a':'done'})
    def test_reclaim_rejects_old_owner(self):
        with tempfile.TemporaryDirectory() as d:
            q=Queue(d+'/queue.db');q.enqueue('t','a',1);q.claim('t','w',0,10)
            self.assertEqual(q.claim('t','other',10,5),('a',1,2))
            self.assertFalse(q.ack('t','a',1,11,'wrong'));self.assertTrue(q.ack('t','a',2,11,'right'))
''',
 'async-cache':'''import asyncio
from app.service import Cache
class Seed(unittest.IsolatedAsyncioTestCase):
    async def test_coalesces_and_closes(self):
        calls=[]
        async def fetch(t,k): calls.append((t,k));await asyncio.sleep(0);return 7
        cache=Cache(fetch,lambda:0,10,2)
        self.assertEqual(await asyncio.gather(cache.get('t','a'),cache.get('t','a')),[7,7])
        self.assertEqual(len(calls),1);await cache.close()
    async def test_expiry_boundary(self):
        clock=[0];calls=[]
        async def fetch(t,k): calls.append(k);return len(calls)
        cache=Cache(fetch,lambda:clock[0],10,2)
        self.assertEqual(await cache.get('t','a'),1);clock[0]=10
        self.assertEqual(await cache.get('t','a'),2);await cache.close()
''',
 'build-planner':'''from app.service import plan
from app.helpers import summarize
class Seed(unittest.TestCase):
    def test_change_propagates(self):
        g={'a':{'deps':[],'stamp':'1'},'b':{'deps':['a'],'stamp':'1'}}
        self.assertEqual(plan(g,g,['a']),{'rebuild':['a','b'],'removed':[]})
        self.assertEqual(summarize(plan(g,g,['a'])),{'count':2,'removed':0})
    def test_rejects_cycle(self):
        g={'a':{'deps':['b'],'stamp':'1'},'b':{'deps':['a'],'stamp':'1'}}
        with self.assertRaises(ValueError):plan(g,g,[])
''',
 'resumable-stream':'''from app.service import Stream
class Seed(unittest.TestCase):
    def test_final_tail(self):
        s=Stream();self.assertEqual(s.feed(b'{"id":"a","value":1}',True),[{'id':'a','value':1}])
        self.assertTrue(s.checkpoint()['finished'])
    def test_atomic_conflict(self):
        s=Stream();s.feed(b'{"id":"a","value":1}\\n');old=s.checkpoint()
        with self.assertRaises(ValueError):s.feed(b'{"id":"b","value":2}\\n{"id":"a","value":3}\\n')
        self.assertEqual(s.checkpoint(),old)
''',
}

def initial(case):
    source=GOLD[case]
    for old,new in REPLACEMENTS[case]:
        source=source.replace(old,new)
    return source
