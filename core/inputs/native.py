"""Bounded identified native attempts; post-only capture never invents a before."""
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import time

from . import bindings,definition
from .collection import capture
from .receipts import attach,hexadecimal
from ..evidence import Result,source_snapshot
from ..hosts.provenance import fingerprint
from ..jobs import ledger_write,Busy
from ..ledger import Ledger,_keep_out_of_git
from ..parsers import parse
from ..payload import command_of
from ..commands import tool_directory,directory_issue

FILE='input-attempts.json'
MAX_BYTES=1024*1024
MAX_PENDING=128
MAX_COMPLETED=256
AGE=3600


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def configured(root):
    policy=Path(root)/definition.FILE
    return policy.exists() or policy.is_symlink()


def identity(payload):
    platform=payload.get('_ep_platform','claude')
    session,call=payload.get('session_id'),payload.get('tool_use_id')
    if (not isinstance(platform,str) or platform not in {'claude','codex','gemini','cursor','copilot'}
            or any(not isinstance(v,str) or not v or len(v)>4096 for v in (session,call))):
        return None
    return digest([platform,session,call])


def invocation(payload,root):
    where=tool_directory(root,payload.get('tool_input') or {})
    return digest([payload.get('tool_name'),command_of(payload),str(where if where is not None else root.resolve())]),directory_issue(root,where)


def configuration(root):
    from ..config import load
    raw=definition.raw(root/'.elevenpowers/config.json',MAX_BYTES,optional=True) or b''
    return digest([hashlib.sha256(raw).hexdigest(),load(root).__dict__])


def timestamp(value):
    return type(value) in (int,float) and 0<=value<=10**12 and math.isfinite(value)


def read(root,deadline):
    bindings.private(root,deadline,filename=FILE)
    data=definition.raw(root/'.elevenpowers'/FILE,MAX_BYTES,optional=True)
    value=definition.decode(data) if data is not None else {
        'schema':1,'project':bindings.identity(root),'pending':{},'completed':{}}
    if (not isinstance(value,dict) or set(value)!={'schema','project','pending','completed'}
            or type(value['schema']) is not int or value['schema']!=1
            or value['project']!=bindings.identity(root)
            or not isinstance(value['pending'],dict) or len(value['pending'])>MAX_PENDING
            or not isinstance(value['completed'],dict) or len(value['completed'])>MAX_COMPLETED):
        raise ValueError('native input state shape or project identity is unavailable')
    for key,row in value['pending'].items():
        if (not hexadecimal(key) or not isinstance(row,dict)
                or set(row)!={'before','source','task','invocation','producer','configuration','created','issues'}
                or any(not hexadecimal(row[k]) for k in ('task','invocation','producer','configuration'))
                or not isinstance(row['source'],str) or len(row['source'])!=16
                or row['before'] is not None and not hexadecimal(row['before'])
                or not timestamp(row['created']) or not isinstance(row['issues'],list)
                or len(row['issues'])>16 or any(not isinstance(i,str) or len(i)>192 for i in row['issues'])):
            raise ValueError('native input attempt metadata is invalid')
    if any(not hexadecimal(k) or not timestamp(v) for k,v in value['completed'].items()):
        raise ValueError('native consumed attempt metadata is invalid')
    return value


@contextmanager
def transaction(root,deadline):
    directory=root/'.elevenpowers'
    if directory.resolve()!=directory.absolute():
        raise ValueError('linked native input state is unsupported')
    directory.mkdir(exist_ok=True);_keep_out_of_git(directory)
    with ledger_write(root,timeout=max(0,min(5,deadline-time.monotonic()))):
        value=read(root,deadline)
        yield value
        data=json.dumps(value,ensure_ascii=True,indent=2).encode()
        if len(data)>MAX_BYTES:
            raise ValueError('native input state write budget exceeded')
        bindings._write(directory/FILE,data)


def before(payload,root):
    root=Path(root).resolve(strict=True)
    if not configured(root): return False
    deadline=time.monotonic()+10
    command=command_of(payload);cwd=tool_directory(root,payload.get('tool_input') or {})
    snapshot=source_snapshot(root,fresh=True,deadline=deadline)
    records=parse(command,'native command completion has not been observed',None,root,snapshot=snapshot,cwd=cwd)
    if not records: return False
    key=identity(payload);ledger=Ledger.load(root);gaps=[]
    observed=capture(root,deadline)
    try:
        final=source_snapshot(root,fresh=True,deadline=deadline)
        if not final[0].complete or final[1]!=snapshot[1] or not snapshot[0].complete:
            gaps.append('Source coverage moved or was incomplete before the command.')
        raw,issue=invocation(payload,root)
        if issue: gaps.append('Command directory does not qualify for this project.')
        if not key or not ledger.task:
            gaps.append('Native command lacks a session, call or task identity.')
        else:
            with transaction(root,deadline) as state:
                if key in state['completed']:
                    gaps.append('A consumed native call identity cannot qualify a new execution.')
                elif key in state['pending']:
                    state['pending'][key]['issues']=['Duplicate before callbacks cannot qualify an execution.']
                    gaps+=state['pending'][key]['issues']
                else:
                    state['pending'][key]={'before':observed['fingerprint'],'source':snapshot[1],
                        'task':digest(ledger.task),'invocation':raw,'producer':fingerprint(),
                        'configuration':configuration(root),'created':time.time(),'issues':gaps}
                while len(state['pending'])>MAX_PENDING:
                    state['pending'].pop(next(iter(state['pending'])))
    except (OSError,ValueError,TimeoutError,Busy):
        gaps.append('Native before observation could not be safely persisted.')
    for item in records:
        item.execution='incomplete';item.result=Result.ERROR
    attach(records,observed,{'state':'incomplete','fingerprint':None},key,gaps)
    ledger.add(records);ledger.save()
    return True


def after(payload,root,records,terminal=True):
    root=Path(root).resolve(strict=True)
    unconfigured=not configured(root)
    state_path=root/'.elevenpowers'/FILE
    if unconfigured and not any(r.external_inputs for r in records) and not (
            state_path.exists() or state_path.is_symlink()): return True
    deadline=time.monotonic()+10
    key=identity(payload);row=None;gaps=[]
    try:
        state=read(root,deadline)
        if key in state['completed']: return False
        row=state['pending'].get(key)
    except (OSError,ValueError,TimeoutError):
        gaps.append('Native input attempt state is unavailable or invalid.')
    if unconfigured and row is None and not any(r.external_inputs for r in records):
        active=any(isinstance(r.external_inputs,dict) and r.external_inputs.get('attempt')==key
                   and r.external_inputs.get('state')=='incomplete' for r in Ledger.load(root).evidence)
        if not active: return True
    observed=capture(root,deadline)
    first={'state':'incomplete','fingerprint':None}
    if row is None:
        gaps.append('No identified native before observation is available.')
    else:
        first={'state':'available' if row['before'] else 'incomplete','fingerprint':row['before']}
        gaps+=row['issues']
        try:
            raw,issue=invocation(payload,root)
            snapshot=source_snapshot(root,fresh=True,deadline=deadline)
            if row['task']!=digest(Ledger.load(root).task) or row['invocation']!=raw or issue:
                gaps.append('Native task or command identity changed during execution.')
            if row['configuration']!=configuration(root) or row['producer']!=fingerprint():
                gaps.append('Command configuration or producer changed during execution.')
            if (snapshot[1]!=row['source'] or not snapshot[0].complete
                    or any(r.tree!=snapshot[1] or r.coverage_issues for r in records)):
                gaps.append('Source inputs moved or coverage was incomplete during execution.')
            if not 0<=time.time()-row['created']<=AGE:
                gaps.append('Native before observation expired or the clock changed.')
            if terminal:
                with transaction(root,deadline) as state:
                    if key in state['completed']: return False
                    if state['pending'].pop(key,None)!=row:
                        gaps.append('Native before state changed during post collection.')
                    state['completed'][key]=time.time()
                    while len(state['completed'])>MAX_COMPLETED:
                        state['completed'].pop(next(iter(state['completed'])))
        except (OSError,ValueError,TimeoutError,Busy):
            gaps.append('Native final input observation is unavailable or incomplete.')
    if not terminal: gaps.append('Native execution has not completed.')
    attach(records,first,observed,key,gaps)
    return True
