"""Separately versioned free audits; never relabel the frozen 94-group scores."""
import asyncio
import base64
import contextlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core.process import run
from eval import hard_archive, hard_cases as cases
from eval.challenge_worker import OutputSink


async def _close_probe(root,two_generations):
    sys.path.insert(0,str(root))
    from app.service import Cache
    futures=[]
    async def fetch(tenant,key):
        future=asyncio.get_running_loop().create_future();futures.append(future)
        return await future
    cache=Cache(fetch,lambda:0,10,2);waiters=[]
    async def start(count):
        waiters.append(asyncio.create_task(cache.get('t','a')))
        for n in range(100):
            if len(futures)>=count:return
            await asyncio.sleep(0)
        raise RuntimeError('fetch did not start')
    await start(1);cache.invalidate('t','a')
    if two_generations:await start(2)
    await cache.close()
    for n in range(10):await asyncio.sleep(0)
    observed={'waiters_done':all(t.done() for t in waiters),'fetches_cancelled':all(f.cancelled() for f in futures)}
    # Explicit cleanup occurs after observations; it cannot make the check pass.
    for future in futures:
        if not future.done():future.cancel()
    for waiter in waiters:
        if not waiter.done():waiter.cancel()
    await asyncio.gather(*waiters,return_exceptions=True)
    return observed


def audit_snapshot(case,snapshot):
    value={'schema_version':1,'case':case,'state':'unavailable','visible':None,'additional':{},'qualified':False}
    try:
        hard_archive._snapshot(case,snapshot)
        if snapshot['state']!='complete':return value
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve()
            for name,encoded in snapshot['files'].items():
                if encoded is None:continue
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(base64.b64decode(encoded,validate=True))
            if not cases.contract(case,root):return value
            try:
                done=run([sys.executable,'-I','-c','import sys,runpy;sys.path.insert(0,sys.argv[1]);runpy.run_path("visible.py",run_name="__main__")',str(root)],cwd=root,timeout=15,shell=False)
                value['visible']={'state':'complete','exit_code':done.returncode}
            except subprocess.TimeoutExpired:
                value['visible']={'state':'timeout','exit_code':None}
            if case=='async-cache':
                for label,both in (('close_detached_fetch',False),('close_old_and_new_fetches',True)):
                    try:
                        done=run([sys.executable,'-I',str(Path(__file__).resolve()),'worker',str(root),str(int(both))],cwd=root,timeout=5,shell=False)
                        observed=json.loads(done.stdout)
                        value['additional'][label]=done.returncode==0 and observed=={'waiters_done':True,'fetches_cancelled':True}
                    except (ValueError,subprocess.SubprocessError):value['additional'][label]=False
            value['state']='audited';value['qualified']=value['visible']=={'state':'complete','exit_code':0} and all(value['additional'].values())
    except (ValueError,OSError,KeyError,TypeError):pass
    return value


def audit_archive(path):
    hard_archive.inspect(path)
    value=hard_archive.benefit_archive._read(path);runs=[]
    for entry in value['runs']:
        r=entry['record'];c=r['case'];proposals=[]
        for h in entry['history']:
            if h.get('phase')!='Stop':continue
            proposals.append({k:audit_snapshot(c,h[k]) for k in ('before','after')})
        runs.append({'case':c,'arm':r['arm'],'state':r['state'],'proposals':proposals,
                     'final':audit_snapshot(c,entry['final_snapshot'])})
    import hashlib
    return {'schema_version':1,'kind':'separate-post-run-audit','auditor_fingerprint':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'limits':['Authored after frozen-run grading; original 94-group scores and identities remain unchanged.',
                      'Visible suite preservation and detached-fetch closure are supplementary checks, not a population effect.',
                      'Interrupted/unqualified native calls remain unqualified even if their saved code passes.'], 'runs':runs}


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='worker':
        with contextlib.redirect_stdout(OutputSink()):
            value=asyncio.run(asyncio.wait_for(_close_probe(Path(sys.argv[2]).resolve(),bool(int(sys.argv[3]))),3))
        print(json.dumps(value,allow_nan=False))
    else:
        import argparse
        from core.export import write
        parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('archive');parser.add_argument('--output',required=True)
        args=parser.parse_args()
        try:
            value=audit_archive(args.archive);write(Path(args.output),json.dumps(value,indent=2,allow_nan=False))
            print(json.dumps({'audited_runs':len(value['runs']),'qualified_final_snapshots':sum(r['final']['qualified'] for r in value['runs'])}))
        except (ValueError,OSError) as error:parser.exit(1,str(error)+'\n')
