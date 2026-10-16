"""Run sealed four-stage references and archives without launching a model."""
import argparse
import json
from pathlib import Path
import time

from core.evidence import source_snapshot
from core.ledger import Ledger
from core.parsers import parse
from . import preservation as p
from .workflow_cases import NAMES, case
from .workflow_oracles import grade
from .workflow_results import publish, reproduce


def rehearse(destination):
    destination=Path(destination).absolute()
    protocol=p.prepare(destination,names=NAMES,seconds=720,model='claude-sonnet-5-5')
    value={'schema':1,'category':'deterministic-four-stage-rehearsal','model_calls':0,
           'installed_acceptance':False,'benefit_comparison':False,
           'scheduled_slots':len(protocol['slots']),'observations':[],
           'runtime':protocol['runtime_fingerprint'],'harness':protocol['harness_sha256'],
           'limits':['Full valid references with actual commands and private source regrades.',
                     'No native agent, installed acceptance or measured coding benefit.']}
    started=time.monotonic()
    for slot in protocol['slots']:
        definition=case(slot.rsplit('-',1)[0]);folder=destination/slot;candidate=folder/'candidate'
        record={'schema':2,'slot':slot,'state':'rehearsed','model_seconds':0,'synthetic_rehearsal':True,'stages':[]}
        for stage in range(1,5):
            p.verify(destination,slot,initial=stage==1)
            (candidate/definition['production'][0]).write_bytes(definition['gold'][stage-1].encode())
            done=p.run(definition['public_command'],cwd=candidate,timeout=30)
            if done.returncode:raise ValueError('reference public command failed')
            ledger=Ledger.load(candidate)
            ledger.add(parse(definition['public_command'],done.stdout+done.stderr,done.returncode,candidate,
                             snapshot=source_snapshot(candidate,fresh=True)))
            ledger.save()
            source={name:(candidate/name).read_bytes().decode('utf8') for name in definition['production']}
            p._write(folder/f'source-{stage}.json',source)
            result=grade(definition,stage,candidate)
            if result['state']!='graded' or result['failed']:raise ValueError('reference independent grade failed')
            record['stages'].append({'stage':stage,'state':'rehearsed','scope':'preserved',
                'seconds_cap':0,'elapsed_ms':0,'conversation_identity':None,
                'host_observation':{'completed':False,'models':[]},'source_after':p._manifest(candidate),
                'independent_grade':result,'native':{'state':'not_run','native_runner_adoption':False}})
            p._write(folder/'result.json',record)
        value['observations'].append({'slot':slot,'stage_passes':[s['independent_grade']['passed'] for s in record['stages']]})
    archive=destination/'source-archive'
    public=publish(archive,{slot:destination for slot in protocol['slots']})
    value['reproduction']=reproduce(archive)
    value['qualified']=value['reproduction']['qualified'] and not public['outcome_comparable']
    value['seconds']=round(time.monotonic()-started,3)
    p._write(destination/'result.json',value)
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    value=rehearse(parser.parse_args().output);print(json.dumps(value,indent=2))
    return 0 if value['qualified'] else 1


if __name__=='__main__':raise SystemExit(main())
