"""Execute candidate behavior; controller owns requests and expected traces."""
import asyncio
import base64
import contextlib
import copy
import json
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from eval.challenge_worker import OutputSink


def lease_queue(module,request):
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'jobs.db';q=module.Queue(path)
        if request.get('concurrent'):
            for n in range(32):
                q.enqueue('t',str(n),n)
            barrier=threading.Barrier(8);answers=[];errors=[];lock=threading.Lock()
            def worker(n):
                try:
                    owned=module.Queue(path);barrier.wait(timeout=5)
                    local=[]
                    while True:
                        item=owned.claim('t',str(n),0,10)
                        if item is None:
                            break
                        local.append(item)
                    with lock:answers.extend(local)
                except BaseException as error:
                    with lock:errors.append(type(error).__name__)
            threads=[threading.Thread(target=worker,args=(n,),daemon=True) for n in range(8)]
            for t in threads:t.start()
            for t in threads:t.join(timeout=8)
            if errors or any(t.is_alive() for t in threads):
                return {'errors':errors,'unfinished':sum(t.is_alive() for t in threads)}
            return {'claimed':len(answers),'unique':len({x[0] for x in answers}),'tokens':sorted({x[2] for x in answers}),'pending':q.pending('t')}
        results=[]
        for name,*args in request['steps']:
            try:
                if name=='reopen':
                    q=module.Queue(path);value=None
                else:
                    value=getattr(q,name)(*args)
                results.append(value)
            except Exception as error:
                results.append({'exception':type(error).__name__})
        return {'results':results,'pending':q.pending('t'),'done':q.results('t')}


async def async_cache(module,name):
    clock=[0];calls=[];futures=[]
    async def immediate(t,k):
        calls.append((t,k));return None if name=='none' else len(calls)
    async def deferred(t,k):
        calls.append((t,k));f=asyncio.get_running_loop().create_future();futures.append(f)
        return await f
    pending_names={'coalesce','completion_ttl','cancel_waiter','invalidate_flight','reverse_completions','double_invalidation','old_cleanup_new_flight','close_pending','all_waiters_cancel','failed_old_new_generation'}
    cache=module.Cache(deferred if name in pending_names else immediate,lambda:clock[0],10,2)
    async def pump(count):
        for n in range(100):
            if len(calls)>=count:return
            await asyncio.sleep(0)
        raise RuntimeError('expected fetch did not start')
    async def start(t='t',k='a',count=None):
        task=asyncio.create_task(cache.get(t,k))
        if count is not None:await pump(count)
        else:
            for n in range(3):await asyncio.sleep(0)
        return task
    async def take(task):
        try:return await asyncio.wait_for(asyncio.shield(task),1)
        except BaseException as error:return type(error).__name__
    try:
        if name in ('basic','none'):
            return [await cache.get('t','a'),await cache.get('t','a'),len(calls)]
        if name=='tenant_isolation':
            return [await cache.get('x','a'),await cache.get('y','a'),await cache.get('x','a'),len(calls)]
        if name=='expiry':
            first=await cache.get('t','a');clock[0]=9;second=await cache.get('t','a');clock[0]=10
            return [first,second,await cache.get('t','a'),len(calls)]
        if name=='coalesce':
            a=await start(count=1);b=await start();futures[0].set_result(1)
            return [[await take(a),await take(b)],len(calls)]
        if name=='completion_ttl':
            a=await start(count=1);clock[0]=20;futures[0].set_result(1);first=await take(a)
            clock[0]=29;hit=await cache.get('t','a');clock[0]=30
            b=await start(count=2);futures[1].set_result(2)
            return [first,hit,await take(b),len(calls)]
        if name in ('cancel_waiter','all_waiters_cancel'):
            a=await start(count=1);b=await start();a.cancel();cancelled=await take(a)
            if name=='all_waiters_cancel':
                b.cancel();other=await take(b)
            if not futures[0].done():futures[0].set_result(1)
            if name=='cancel_waiter':return [cancelled,await take(b),len(calls)]
            for n in range(5):await asyncio.sleep(0)
            return [cancelled,other,await cache.get('t','a'),len(calls)]
        if name=='failure_retry':
            attempts=[0]
            async def fail(t,k):
                attempts[0]+=1
                if attempts[0]==1:raise LookupError('upstream')
                return attempts[0]
            cache.fetch=fail
            try:await cache.get('t','a');first='no-error'
            except Exception as error:first=type(error).__name__
            return [first,await cache.get('t','a'),attempts[0]]
        if name=='invalidate_cached':
            a=await cache.get('t','a');cache.invalidate('t','a')
            return [a,await cache.get('t','a'),len(calls)]
        if name in ('invalidate_flight','reverse_completions','old_cleanup_new_flight','failed_old_new_generation'):
            a=await start(count=1);cache.invalidate('t','a');b=await start(count=2)
            if name=='reverse_completions':
                futures[1].set_result(2);new=await take(b);futures[0].set_result(1);old=await take(a)
                return [new,old,await cache.get('t','a'),len(calls)]
            if name=='failed_old_new_generation':futures[0].set_exception(LookupError('old'))
            else:futures[0].set_result(1)
            old=await take(a)
            if name=='old_cleanup_new_flight':
                c=await start();futures[1].set_result(2)
                return [old,await take(b),await take(c),len(calls)]
            futures[1].set_result(2);new=await take(b)
            return [old,new,await cache.get('t','a'),len(calls)]
        if name=='double_invalidation':
            a=await start(count=1);cache.invalidate('t','a');b=await start(count=2)
            cache.invalidate('t','a');c=await start(count=3)
            futures[0].set_result(1);old=await take(a);futures[2].set_result(3);new=await take(c)
            futures[1].set_result(2);middle=await take(b)
            return [old,middle,new,await cache.get('t','a'),len(calls)]
        if name=='lru_hit':
            values=[await cache.get('t',key) for key in ('a','b','a','c','a','b')]
            return values+[len(calls)]
        if name=='tenant_invalidation':
            a=await cache.get('x','a');b=await cache.get('y','a');cache.invalidate('x','a')
            return [a,b,await cache.get('y','a'),await cache.get('x','a'),len(calls)]
        if name=='close_pending':
            a=await start(count=1);await cache.close();cancelled=await take(a)
            try:await cache.get('t','a');get='no-error'
            except Exception as error:get=type(error).__name__
            try:cache.invalidate('t','a');inv='no-error'
            except Exception as error:inv=type(error).__name__
            return [cancelled,get,inv,len(calls)]
        if name=='close_idempotent':
            await cache.close();await cache.close()
            try:await cache.get('t','a');return ['no-error']
            except Exception as error:return [type(error).__name__]
        if name in ('invalid_ttl','invalid_capacity'):
            values=[0,-1,True,float('inf'),float('nan')] if name=='invalid_ttl' else [0,-1,True,1.5]
            results=[]
            for value in values:
                try:module.Cache(immediate,lambda:0,value if name=='invalid_ttl' else 10,value if name=='invalid_capacity' else 2);results.append('no-error')
                except Exception as error:results.append(type(error).__name__)
            return results
        if name=='invalid_key':
            results=[]
            for t,k in (('','a'),('t',''),(True,'a'),('t',None)):
                try:await cache.get(t,k);results.append('no-error')
                except Exception as error:results.append(type(error).__name__)
            return results
        raise ValueError('unknown scenario')
    finally:
        await cache.close()


def build_planner(module,request):
    from app.helpers import summarize
    old,new,changed=request['old'],request['new'],request['changed']
    original=copy.deepcopy([old,new,changed])
    try:
        result=module.plan(old,new,changed)
        return {'result':result,'unchanged_inputs':[old,new,changed]==original,'summary':summarize(result)}
    except Exception as error:return {'exception':type(error).__name__}


def resumable_stream(module,request):
    from app.helpers import commit
    if request.get('special')=='closed':
        s=module.Stream();s.feed(b'',True)
        try:s.feed(b'');return ['no-error']
        except Exception as error:return [type(error).__name__]
    if request.get('special')=='invalid_checkpoints':
        base={'offset':0,'pending':'','seen':{},'finished':False};values=[
            {**base,'offset':True},{**base,'pending':'!'}, {**base,'pending':'YQ=='},
            {**base,'seen':{'a':'bad'}},{**base,'seen':{'':'["int",1]'}},
            {**base,'offset':1,'pending':'YQ==','finished':True},{**base,'extra':1}]
        results=[]
        for value in values:
            try:module.Stream(value);results.append('no-error')
            except Exception as error:results.append(type(error).__name__)
        return results
    if request.get('special')=='sink_retry':
        old=module.Stream().checkpoint();before=copy.deepcopy(old);outputs=[];chunk=b'{"id":"a","value":1}\n'
        def fail(records):outputs.append(records);raise LookupError('sink failed')
        try:commit(old,chunk,fail);error='no-error'
        except Exception as err:error=type(err).__name__
        new=commit(old,chunk,outputs.append)
        return {'first_error':error,'unchanged':old==before,'outputs':outputs,'offset':new['offset']}
    s=module.Stream();outputs=[];errors=[];rollback=True;detached=True;restored=True
    for n,chunk in enumerate(request['chunks']):
        old=s.checkpoint();untouched=copy.deepcopy(old)
        try:
            output=s.feed(base64.b64decode(chunk),request['final'] and n==len(request['chunks'])-1);error=''
        except Exception as err:
            output=[];error=type(err).__name__;rollback &= s.checkpoint()==untouched
        outputs.append(output);errors.append(error);detached &= old==untouched
        current=s.checkpoint();copy_state=copy.deepcopy(current)
        current['seen']['_detachment_probe']='["int",0]'
        detached &= s.checkpoint()==copy_state
        s=module.Stream(copy_state);restored &= s.checkpoint()==copy_state
    state=s.checkpoint()
    return {'outputs':outputs,'errors':errors,'offset':state['offset'],'pending':state['pending'],'seen':state['seen'],'finished':state['finished'],'rollback':rollback,'detached':detached,'restored':restored}


def main(root,case,requests):
    sys.path.insert(0,str(root))
    from app import service
    results=[]
    for request in requests:
        try:
            if case=='async-cache':value=asyncio.run(asyncio.wait_for(async_cache(service,request['scenario']),3))
            else:value={'lease-queue':lease_queue,'build-planner':build_planner,'resumable-stream':resumable_stream}[case](service,request)
            # JSON serialization removes tuples but never conflates bool/int here.
            results.append(value)
        except BaseException as error:results.append({'worker_exception':type(error).__name__})
    return {'responses':results}


if __name__=='__main__':
    with contextlib.redirect_stdout(OutputSink()):
        value=main(Path(sys.argv[1]).resolve(),sys.argv[2],json.loads(sys.argv[3]))
    print(json.dumps(value,allow_nan=False))
