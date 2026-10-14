"""Actual two-command scope/reuse/read-cost controls; no model calls."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

from core.config import Config, save
from core.hosts.provenance import fingerprint
from core.inputs import definition
from core.ledger import Ledger
from core.patchproof.execution import verify
from core.patchproof.planning import plan
from core.patchproof.report import build
from core.export import build as report
from .external_inputs import project as dependency_project
from .github_presentation import _git
from .input_sessions import HOSTS, native


def project(directory,language,*,scoped=True):
    root,_,_,target,good,bad,args,command=dependency_project(directory,language)
    other=target.with_name('other'+target.suffix);other.write_bytes(good)
    script=root/args[-1];second=script.with_name('other'+script.suffix)
    second.write_text(script.read_text(encoding='utf-8').replace(repr(str(target)),repr(str(other)))
        .replace(json.dumps(str(target)),json.dumps(str(other))).replace('count.txt','other-count.txt'),encoding='utf-8')
    other_args=[*args[:-1],second.name]
    other_command=subprocess.list2cmdline(other_args) if os.name=='nt' else shlex.join(other_args)
    commands=[command,other_command]
    policy={'schema':2 if scoped else 1,'witnesses':[
        {'id':'first','root':'deps','paths':[target.name]},
        {'id':'second','root':'deps','paths':[other.name]}]}
    if scoped:
        policy['commands']=[{'command':c,'witnesses':[name],'complete':True}
                            for c,name in zip(commands,['first','second'])]
    (root/definition.FILE).write_text(json.dumps(policy),encoding='utf-8')
    save(root,Config(auto_detect=False,commands={'tests':command,'build':other_command}))
    (root/'elevenpowers.milestones.json').write_text(json.dumps({'schema':1,'milestones':[
        {'id':name,'description':name+' returns two','inputs':['service.py'],
         'checks':[{'kind':kind,'command':c}]} for name,kind,c in
        zip(['first','second'],['test_suite','build'],commands)]}),encoding='utf-8')
    _git(root,'add','.');_git(root,'commit','-qm','independent consumers')
    base=_git(root,'rev-parse','HEAD')
    (root/'service.py').write_bytes(b'value=3\n')
    _git(root,'add','.');_git(root,'commit','-qm','source change')
    head=_git(root,'rev-parse','HEAD')
    return root,base,head,target,other,good,bad,[args,other_args],commands


def counts(root):
    return [int((root/'.elevenpowers'/p).read_text()) for p in ('count.txt','other-count.txt')]


def case(directory,language,*,scoped=True):
    root,base,head,target,other,good,bad,args,commands=project(directory,language,scoped=scoped)
    native_states=[]
    if scoped:
        Ledger(root=root,task='first task').save()
        for host in HOSTS:
            for n in range(2): native(root,args[n],commands[n],host,host+str(n))
        Ledger(root=root,task='next task').save()
        native_states=[m['state'] for m in report(root)['milestones']['milestones']]
        if native_states!=['CURRENT','CURRENT']: raise ValueError('native retained scopes lost current evidence')
    first=verify(root,base,head,seconds=180,command_seconds=15)
    sequence=[counts(root)]
    target.write_bytes(bad)
    independent=subprocess.run(args[0],cwd=root,capture_output=True,timeout=15)
    if independent.returncode==0: raise ValueError('independent fault was not detected')
    choice=plan(root,base,head,seconds=180)
    actions={c['properties'][0]:c['action'] for c in choice['checks']}
    failed=verify(root,base,head,seconds=180,command_seconds=15);sequence.append(counts(root))
    target.write_bytes(good)
    repaired=verify(root,base,head,seconds=180,command_seconds=15);sequence.append(counts(root))
    reads={target:0,other:0};original=definition.raw
    def counted(path,*args,**kwargs):
        if path in reads: reads[path]+=1
        return original(path,*args,**kwargs)
    definition.raw=counted
    try: bundle=build(root,base,head,timeout=180)
    finally: definition.raw=original
    target.unlink()
    missing=report(root,timeout=120)
    associations={r['declaration']:r['external_inputs']['state'] for r in missing['receipts'] if r['declaration']}
    expected_actions={'tests':'run','build':'reuse' if scoped else 'run'}
    offset=5 if scoped else 0
    expected=[[offset+1,offset+1],[offset+3,offset+(1 if scoped else 2)],
              [offset+4,offset+(1 if scoped else 3)]]
    if (first['state']!='passed' or failed['state']!='failed' or repaired['state']!='passed'
            or actions!=expected_actions or sequence!=expected or list(reads.values())!=[2,2]
            or associations['tests']!='incomplete' or associations['build']!=('bound' if scoped else 'incomplete')
            or bundle['binding']['state']!='bound'):
        raise ValueError('scope/reuse/closure acceptance failed: '+repr((actions,sequence,reads,associations)))
    return {'language':language,'scoped':scoped,'native_retained':native_states,
            'outcomes':[first['state'],failed['state'],repaired['state']],
            'drift_actions':actions,'command_counts':sequence,'reads_per_file':list(reads.values()),
            'missing_associations':associations,'independent_bad_exit':independent.returncode}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    options=parser.parse_args(argv);destination=options.output.absolute()
    if destination.exists() or destination.is_symlink(): raise ValueError('acceptance destination must be new')
    destination.mkdir(parents=True)
    started=time.monotonic();rows=[]
    for language in ('python','javascript'):
        for scoped in (True,False):
            slot=destination/(language+('-scoped' if scoped else '-broad'));slot.mkdir()
            rows.append(case(slot,language,scoped=scoped))
            print(json.dumps({'phase':'case_completed','language':language,'scoped':scoped}),flush=True)
    value={'schema':1,'category':'actual-command-controlled-scope-exercise','runtime':fingerprint(),
           'observations':rows,'seconds':round(time.monotonic()-started,3),'model_calls':0,
           'limits':['Synthetic host envelopes are not installed host acceptance.',
                     'Two selected local consumers per language; no full environment or population benefit claim.']}
    (destination/'result.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
    print(json.dumps(value,indent=2))


if __name__=='__main__': main()
