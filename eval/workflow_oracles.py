"""Independent observable contracts, executed from fresh private source copies."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import math

from core.process import run


PY_GROUPS = [
('core',0,'''q=Queue();q.enqueue('x',{'v':1});q.enqueue('x',{'v':9})
assert q.claim('missing') is None
assert q.claim('x')==({'v':1},1) and q.claim('x') is None
assert not q.ack('x',99) and q.ack('x',1) and q.claim('x') is None'''),
('formatting',0,"assert render(42)=='42' and render('x')=='x'"),
('lease_expiry',1,'''q=Queue();q.enqueue('x',1)
assert q.claim('x',0,2)==(1,1) and q.claim('x',1,2) is None
assert q.claim('x',2,3)==(1,2) and not q.ack('x',1) and q.ack('x',2)'''),
('retry_limits',1,'''q=Queue(max_attempts=2);q.enqueue('x',1)
t=q.claim('x')[1];assert q.retry('x',t) and not q.retry('x',t)
t2=q.claim('x')[1];assert t2>t and q.retry('x',t2) and q.claim('x',100) is None
q=Queue();q.enqueue('x',1)
try: q.claim('x',0,0)
except ValueError: pass
else: assert False
assert q.claim('x')==(1,1)'''),
('restart_fencing',2,'''q=Queue();q.enqueue('x',{'v':1});t=q.claim('x',5,3)[1]
saved=q.dumps();r=Queue.loads(saved);assert r.claim('x',7) is None
next_token=r.claim('x',8)[1];assert next_token>t and not r.ack('x',t)
assert r.ack('x',next_token) and q.claim('x',7) is None
assert json.loads(saved)['version']==2'''),
('snapshot_validation',2,'''for bad in ('{','[]','{}','{"version":99}'):
    try: Queue.loads(bad)
    except ValueError: pass
    else: assert False
q=Queue(1);q.enqueue('x',1);q.retry('x',q.claim('x')[1]);r=Queue.loads(q.dumps())
assert r.claim('x',100) is None'''),
('batch_atomicity',3,'''q=Queue();q.enqueue('x',1);q.enqueue('y',2)
before=q.dumps();assert q.batch(['x','missing']) is None and q.dumps()==before
rows=q.batch(['x','y']);assert rows=={'x':(1,1),'y':(2,2)}
assert q.claim('x') is None and q.batch([])=={}'''),
('dead_and_batch_validation',3,'''q=Queue(1);q.enqueue('x',1);t=q.claim('x')[1];assert q.retry('x',t) and q.dead('x')
before=q.dumps()
try:q.batch(['x','x'])
except ValueError:pass
else:assert False
assert q.dumps()==before and not q.dead('unknown')'''),
('replay_identity',4,'''q=Queue();events=[{'event':'a','op':'enqueue','args':['x',1]},{'event':'b','op':'claim','args':['x',0,2]}]
q.replay(events);r=Queue.loads(q.dumps());before=r.dumps();r.replay(events)
assert r.dumps()==before
conflict=[{'event':'a','op':'enqueue','args':['other',2]}]
try:r.replay(conflict)
except ValueError:pass
else:assert False
assert r.dumps()==before'''),
('migration_and_replay_atomicity',4,'''r=Queue.loads(json.dumps({'version':1,'serial':9,'items':{'x':{'payload':4,'done':False,'token':9}}}))
assert r.claim('x',10**31) is None and r.retry('x',9) and r.claim('x')[1]>9
before=r.dumps()
try:r.replay([{'event':'a','op':'enqueue','args':['y',1]},{'event':'b','op':'unknown','args':[]}])
except ValueError:pass
else:assert False
assert r.dumps()==before''')]


JS_GROUPS = [
('core',0,"const o=new Orders({x:4,y:2});assert.equal(o.reserve('a','x',3),true);assert.equal(o.reserve('a','x',3),true);assert.equal(o.reserve('a','x',2),false);assert.equal(o.available('x'),1);assert.equal(o.reserve('b','x',2),false);assert.equal(o.available('y'),2);"),
('formatting',0,"assert.equal(render(42),'42');assert.equal(render('x'),'x');"),
('hold_expiry',1,"const o=new Orders({x:4});o.reserve('a','x',3,5,2);assert.equal(o.available('x',6),1);assert.equal(o.reserve('a','x',3,6,9),true);assert.equal(o.available('x',7),4);assert.equal(o.reserve('a','x',3,7,2),false);o.expire(8);assert.equal(o.available('x'),4);"),
('hold_validation',1,"const o=new Orders({x:4});o.reserve('a','x',2,0,1);assert.throws(()=>o.reserve('b','x',0,10),RangeError);assert.equal(o.available('x'),2);assert.equal(o.available('x',1),4);assert.throws(()=>o.reserve('b','x',1,1,0),RangeError);"),
('exact_refunds',2,"const o=new Orders({x:5},{x:'9007199254740993'});o.reserve('a','x',3);assert.equal(o.fulfill('a',2),18014398509481986n);assert.equal(o.refund('a',1),9007199254740993n);assert.equal(o.refund('a',2),null);assert.equal(o.available('x',10),4);assert.equal(o.refund('a',1),9007199254740993n);assert.equal(o.available('x'),5);"),
('fulfillment_rejection',2,"const o=new Orders({x:2},{x:'19'});o.reserve('a','x',2);assert.equal(o.fulfill('a',3),null);assert.equal(o.fulfill('a',1),19n);assert.equal(o.available('x',10),1);assert.equal(o.fulfill('a',1,10),null);assert.throws(()=>o.refund('a',0),RangeError);"),
('restart_identity',3,"const o=new Orders({x:4},{x:'7'});o.reserve('a','x',3,5,2);const r=Orders.loads(o.dumps());assert.equal(r.reserve('a','x',3,6,10),true);assert.equal(r.available('x',7),4);assert.equal(o.available('x'),1);assert.equal(r.reserve('a','x',3,8),false);assert.equal(JSON.parse(r.dumps()).version,2);"),
('snapshot_validation',3,"for(const bad of ['{','[]','{}','{\"version\":99}']) assert.throws(()=>Orders.loads(bad),RangeError);const o=new Orders({x:3},{x:'11'});o.reserve('a','x',2);o.fulfill('a',1);const r=Orders.loads(o.dumps());assert.equal(r.refund('a',1),11n);assert.equal(r.refund('a',1),null);"),
('batch_replay',4,"const o=new Orders({x:4},{x:'9'});const es=[{event:'a',op:'reserve',args:['h','x',2]},{event:'b',op:'fulfill',args:['h',1]}];o.replay(es);const r=Orders.loads(o.dumps());const before=r.dumps();r.replay(es);assert.equal(r.dumps(),before);assert.throws(()=>r.replay([{event:'a',op:'expire',args:[100]}]),RangeError);assert.equal(r.dumps(),before);"),
('replay_atomicity',4,"const o=new Orders({x:4});const before=o.dumps();assert.throws(()=>o.replay([{event:'a',op:'reserve',args:['h','x',2]},{event:'b',op:'missing',args:[]}]),RangeError);assert.equal(o.dumps(),before);assert.throws(()=>o.replay([{event:'c',op:'reserve',args:['h','x',9]}]),RangeError);assert.equal(o.dumps(),before);")]


def oracle(value, stage):
    if type(stage) is not int or not 0<=stage<=4 or value['id'] not in ('workflow-queue-py','workflow-orders-js'):
        raise ValueError('invalid four-stage oracle')
    python=value['language']=='python';groups=PY_GROUPS if python else JS_GROUPS
    selected=[g for g in groups if g[1]<=stage]
    if python:
        return ('import sys,json\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).parent))\n'
                'from service import Queue\nfrom formatting import render\nrows=[]\n'
                f'for name,introduced,code in {selected!r}:\n'
                '    try:\n        exec(code,globals(),{})\n        state="passed"\n'
                '    except Exception:\n        state="failed"\n'
                '    rows.append({"id":name,"introduced_stage":introduced,"state":state})\nprint(json.dumps(rows))\n')
    return ("const assert=require('node:assert/strict'),{Orders}=require('./service.cjs'),{render}=require('./formatting.cjs');\nconst rows=[];\n"
            f'for(const [id,introduced_stage,code] of {json.dumps(selected)}) {{\n'
            "let state='passed';try{new Function('Orders','render','assert',code)(Orders,render,assert);}catch(e){state='failed';}\nrows.push({id,introduced_stage,state});}\nconsole.log(JSON.stringify(rows));\n")


def grade(value,stage,candidate,*,seconds=15):
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<seconds<=30:
        raise ValueError('invalid grading allowance')
    source=oracle(value,stage);started=time.monotonic()
    result={'state':'incomplete','groups':[],'checks':[],'passed':0,'failed':0,'source_sha256':{},
            'oracle_sha256':hashlib.sha256(source.encode()).hexdigest(),'elapsed_ms':0}
    try:
        from .preservation import _safe
        with tempfile.TemporaryDirectory(prefix='ep-workflow-grade-') as folder:
            private=Path(folder)
            for name in value['production']:
                path=_safe(Path(candidate),name)
                if not path.is_file() or path.stat().st_size>256*1024: return result
                data=path.read_bytes();result['source_sha256'][name]=hashlib.sha256(data).hexdigest()
                (private/name).write_bytes(data)
            python=value['language']=='python';engine=sys.executable if python else shutil.which('node')
            if not engine: result['state']='setup';return result
            script=private/('_oracle.py' if python else '_oracle.cjs');script.write_bytes(source.encode())
            done=run([engine,*(['-I','-B'] if python else []),str(script)],cwd=private,shell=False,timeout=seconds)
            if done.returncode: result['state']='setup';return result
            rows=json.loads(done.stdout);expected=[g for g in (PY_GROUPS if python else JS_GROUPS) if g[1]<=stage]
            if (not isinstance(rows,list) or [(r.get('id'),r.get('introduced_stage')) for r in rows]!=[(g[0],g[1]) for g in expected]
                    or any(r.get('state') not in ('passed','failed') for r in rows)): return result
            result.update(state='graded',groups=rows,checks=rows,passed=sum(r['state']=='passed' for r in rows),
                          failed=sum(r['state']=='failed' for r in rows))
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError):
        pass
    finally: result['elapsed_ms']=round((time.monotonic()-started)*1000,3)
    return result
