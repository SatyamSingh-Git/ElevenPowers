"""Actual project-independent batch checks with synthetic native guidance/callbacks."""
import argparse
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from core.check_batch import execute
from core.evidence import Result
from core.hook import dispatch
from core.hosts.provenance import fingerprint
from core.hosts.readiness import ingress
from core.ledger import Ledger
from core.milestones import build
from .declared_checks import CLI, _outer
from .input_scopes import counts, project
from .input_sessions import HOSTS


def _advice(root):
    output=io.StringIO()
    def observed_counts():
        paths=[root/'.elevenpowers'/p for p in ('count.txt','other-count.txt')]
        return [int(p.read_text()) if p.exists() else 0 for p in paths]
    before=observed_counts()
    with redirect_stdout(output),ingress('host'):
        dispatch('UserPromptSubmit',{'cwd':str(root),'session_id':'synthetic-batch-control',
            'prompt':'This is a new task. Verify the dependency without editing any file.'})
    context=json.loads(output.getvalue())['hookSpecificOutput']['additionalContext']
    return {'emitted':bool('Owned check arguments:' in context and '--all' in context),
            'characters':len(context),'sha256':hashlib.sha256(context.encode()).hexdigest(),
            'launched_nothing':observed_counts()==before}


def _states(root):
    return [row['state'] for row in build(root)['milestones']]


def case(directory,language):
    directory=Path(directory).absolute()
    directory.mkdir(parents=True)
    root,base,head,target,other,good,bad,args,commands=project(directory,language)
    Ledger(root=root,task='batch-control').save()
    advice=_advice(root)
    values=[execute(root)]
    snapshots=[_states(root)]
    target.write_bytes(bad)
    snapshots.append(_states(root))
    invocation=f'"{sys.executable}" "{CLI}" --all --project "{root}" --json'
    shell=invocation+(' & echo outer-complete' if os.name=='nt' else '; echo outer-complete')
    outer=subprocess.run(shell,cwd=root,shell=True,capture_output=True,text=True,timeout=60)
    failed=json.loads(outer.stdout[:outer.stdout.rfind('}')+1])
    values.append(failed)
    for host in HOSTS:
        _outer(root,shell,host,outer.stdout)
    records=[e for e in Ledger.load(root).evidence if e.declaration=='tests' and e.kind.value=='test_suite']
    survived=bool(records and records[-1].result is Result.FAIL and records[-1].execution=='complete')
    snapshots.append(_states(root))
    target.write_bytes(good)
    values.append(execute(root));snapshots.append(_states(root))
    before_missing=counts(root)
    target.unlink()
    missing=execute(root);values.append(missing)
    after_missing=counts(root)
    outcomes=[[r['state'] for r in value['results']] for value in values]
    value={'language':language,'outcomes':outcomes,'aggregate_states':[v['state'] for v in values],
           'milestones':snapshots,'counts_before_missing':before_missing,'counts_after_missing':after_missing,
           'outer_shell_exit':outer.returncode,'owned_failure_survived_callbacks':survived,
           'synthetic_hosts':HOSTS,'new_task_guidance_emitted':advice['emitted'],
           'advice_characters':advice['characters'],'advice_sha256':advice['sha256'],
           'advice_launched_nothing':advice['launched_nothing'],
           'missing_property_unrun':missing['results'][0]['unrun'],
           'model_calls':0,'installed_acceptance':False}
    value['qualified']=(outcomes==[['passed','passed'],['failed','passed'],['passed','passed'],['incomplete','passed']]
        and snapshots==[['CURRENT','CURRENT'],['STALE','CURRENT'],['FAILED','CURRENT'],['CURRENT','CURRENT']]
        and before_missing==[3,3] and after_missing==[3,4] and survived and outer.returncode==0
        and advice['emitted'] and advice['launched_nothing'] and advice['characters']<=2000
        and value['missing_property_unrun'])
    return value


def exercise(destination):
    destination=Path(destination).absolute()
    if destination.exists() or any(p.is_symlink() or getattr(p,'is_junction',lambda:False)()
                                  for p in (destination,*destination.parents)):
        raise ValueError('exercise requires a new unlinked directory')
    destination.mkdir(parents=True)
    started=time.monotonic();before=fingerprint()
    value={'schema_version':1,'producer':before,'model_calls':0,'installed_acceptance':False,
           'observations':[case(destination/language,language) for language in ('python','javascript')],
           'limits':['Actual Python/Node child processes with synthetic guidance and outer-host callbacks.',
                     'No installed-model acceptance, causal coding benefit or exhaustive dependency coverage.']}
    value['qualified']=all(v['qualified'] for v in value['observations']) and before==fingerprint()
    value['seconds']=round(time.monotonic()-started,3)
    (destination/'result.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    value=exercise(parser.parse_args().output)
    print(json.dumps(value,indent=2))
    return 0 if value['qualified'] else 1


if __name__=='__main__':
    raise SystemExit(main())
