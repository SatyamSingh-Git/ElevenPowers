"""Explicit subscription review of frozen inputs; no installation-time calls."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time

from core.process import run, OutputLimitExceeded
from . import subscription
from .review_checkpoint import prepare, capture_additions


def prompt(case, arm, feedback, python):
    text=f'''Review the saved production change in this repository and strengthen its behavioral tests.
The production code and existing tests are fixed inputs. Only ADD new tests/**/test_*.py files.
Do not edit existing files, source, configuration, documentation, Git state or host settings.
Inspect the current diff and public contracts. Add useful boundary/error/preservation tests;
avoid assertions about source spelling, instrumentation, mutation IDs or implementation trivia.
There may be no missing test worth adding. Do not invent a defect or weaken assertions.
Run the full suite with: "{python}" ep_review_pytest.py tests -q -p no:cacheprovider
Work only inside this directory. Do not fetch upstream answers, read other workspaces,
install dependencies, use network tools or delegate to another model. Report what you tested.
The requested change was: {case.get('purpose','the saved production patch')}.
'''
    if arm=='assisted':
        text+='\nAdditional ElevenPowers observations:\n'+feedback+'\n'
    return text


def review(case, arm, feedback, destination, executable, *, python=None,
           model='claude-sonnet-5', seconds=480):
    import sys
    if arm not in ('ordinary','assisted') or type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<seconds<=480:
        raise ValueError('invalid review arm or budget')
    if model not in subscription.SUPPORTED_MODELS['claude'] or len(feedback.encode('utf-8'))>64*1024:
        raise ValueError('invalid review model or feedback')
    destination=Path(destination).absolute()
    if destination.exists() or any(p.is_symlink() for p in (destination,*destination.parents)):
        raise ValueError('existing or linked review slot cannot be reused')
    destination.mkdir(parents=True)
    value={'schema_version':1,'case':case['id'],'arm':arm,'state':'preparing',
           'requested_model':model,'effort':'medium','seconds_cap':seconds,'elapsed_ms':0,
           'host_observation':None,'additions':{},'scope':'not_checked','launch_attempted':False,
           'input_seal':{},'prompt_sha256':'','feedback_sha256':hashlib.sha256(feedback.encode()).hexdigest() if arm=='assisted' else '',
           'exposure_boundary':'native tools; no OS sandbox or closed-book claim',
           'customization':'Claude safe mode; no external MCP; file and Bash tools only'}

    def persist():
        path=destination/'result.json'; temporary=destination/'result.tmp'
        temporary.write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf-8')
        temporary.replace(path)

    persist()
    root=destination/'candidate'
    try:
        expected=prepare(case,root)
        value['input_seal']=expected
        text=prompt(case,arm,feedback,python or sys.executable)
        value['prompt_sha256']=hashlib.sha256(text.encode()).hexdigest()
        (destination/'prompt.txt').write_text(text,encoding='utf-8')
        if not subscription.auth('claude',executable,root):
            value['state']='authentication_unavailable';persist();return value
        args=subscription.command('claude',executable,root,text,model=model)
        args[args.index('--output-format')+1]='stream-json'
        args += ['--verbose','--safe-mode','--disable-slash-commands',
                 '--disallowedTools','WebFetch','WebSearch','Agent',
                 'Bash(curl *)','Bash(wget *)','Bash(git fetch *)','Bash(git clone *)',
                 'Bash(pip install *)','Bash(npm install *)']
        value['state']='running';value['launch_attempted']=True;persist()
        started=time.monotonic();stdout='';stderr='';code=None
        try:
            done=run(args,cwd=root,timeout=seconds,shell=False)
            stdout,stderr,code=done.stdout,done.stderr,done.returncode
            value['state']='returned' if code==0 else 'host_failed'
        except (subprocess.TimeoutExpired,OutputLimitExceeded,OSError) as exc:
            stdout=getattr(exc,'stdout','') or '';stderr=getattr(exc,'stderr','') or ''
            if isinstance(stdout,bytes): stdout=stdout.decode('utf-8','replace')
            if isinstance(stderr,bytes): stderr=stderr.decode('utf-8','replace')
            value['state']='timeout' if isinstance(exc,subprocess.TimeoutExpired) else 'output_limit' if isinstance(exc,OutputLimitExceeded) else 'host_unavailable'
        value['elapsed_ms']=round((time.monotonic()-started)*1000,3)
        value['exit_code']=code
        (destination/'native.jsonl').write_text(stdout,encoding='utf-8')
        (destination/'diagnostic.txt').write_text(stderr,encoding='utf-8')
        result=''
        for line in stdout.splitlines():
            try:
                event=json.loads(line)
                if event.get('type')=='result':result=json.dumps(event)
            except (ValueError,AttributeError):
                continue
        value['host_observation']=subscription.observation('claude',result,stderr)
        if value['state']=='returned':
            value['state']='completed' if value['host_observation']['completed'] else 'host_incomplete'
        try:
            value['additions']=capture_additions(root,expected)
            value['scope']='preserved'
        except (ValueError,OSError,UnicodeError):
            value['scope']='violated';value['state']='scope_violation'
        persist()
        return value
    except (ValueError,OSError,subprocess.SubprocessError):
        value['state']='preparation_failed';persist();raise


def main():
    import argparse
    import sys
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',type=Path,required=True,help='frozen case JSON; no evaluator fixtures')
    parser.add_argument('--repository',type=Path,required=True,help='local cache with the pinned base commit')
    parser.add_argument('--arm',choices=('ordinary','assisted'),required=True)
    parser.add_argument('--feedback',type=Path,help='function-level brief for assisted review')
    parser.add_argument('--destination',type=Path,required=True,help='new private directory; never reused')
    parser.add_argument('--executable',required=True,help='explicit installed Claude subscription CLI')
    parser.add_argument('--python',default=sys.executable,help='interpreter with upstream test dependencies')
    parser.add_argument('--seconds',type=float,default=480)
    args=parser.parse_args()
    try:
        if args.case.stat().st_size>4*1024*1024 or (args.feedback and args.feedback.stat().st_size>64*1024):
            raise ValueError('review input exceeds bounds')
        case=json.loads(args.case.read_text(encoding='utf-8'))
        case['repository']=str(args.repository.resolve(strict=True))
        if args.arm=='assisted' and args.feedback is None:
            raise ValueError('assisted review requires its frozen feedback brief')
        feedback=args.feedback.read_text(encoding='utf-8') if args.feedback else ''
        value=review(case,args.arm,feedback,args.destination,args.executable,
                     python=args.python,seconds=args.seconds)
        print(json.dumps({key:value[key] for key in ('case','arm','state','scope','elapsed_ms','host_observation')}))
        return 0 if value['state']=='completed' else 2
    except (ValueError,OSError,subprocess.SubprocessError):
        parser.exit(2,'Review could not complete; inspect the private slot journal if created.\n')


if __name__=='__main__':
    raise SystemExit(main())
