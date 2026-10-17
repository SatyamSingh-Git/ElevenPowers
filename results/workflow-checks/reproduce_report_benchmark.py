"""Explicit source-only report ablation; no model, host or project check."""
import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(SOURCE))
from core.config import Config,save
from core.evidence import Evidence,Kind,Result,source_snapshot
from core.ledger import Ledger
from core.obligations import Claim
import core.report as report
import core.evidence as evidence
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--receipts',type=int,default=5,choices=range(1,33),
                    help='Source-wide receipts per report (default: 5); one exposes the closing-guard cost.')
options=parser.parse_args()
if options.output.exists() or options.output.is_symlink():
    raise ValueError('Use a new output file; original measurements must remain unchanged.')
if os.name=='nt':tempfile.tempdir=str(Path(os.environ['SystemRoot'])/'Temp')
rows=[]
for language,suffix in (('python','.py'),('javascript','.cjs')):
    for repeat in range(3):
        order=('legacy','optimized') if repeat%2==0 else ('optimized','legacy')
        for mode in order:
            root=Path(tempfile.mkdtemp(prefix='ep-report-bench-'))
            for index in range(150):(root/f'file{index}{suffix}').write_bytes(b'value = 1\n' if suffix=='.py' else b'exports.value=1;\n')
            subprocess.run(['git','init','-q'],cwd=root,check=True,capture_output=True)
            save(root,Config(profile='guide',auto_detect=False,strength={'enabled':False}))
            scan,tree=source_snapshot(root,fresh=True)
            ledger=Ledger(root=root,task='report-work',claims=[Claim.DOCS_CHANGED])
            ledger.evidence=[Evidence(kind=Kind.SUITE,identity=f'suite-{i}',result=Result.PASS,
                scope='source',observed=scan.files,tree=tree) for i in range(options.receipts)]
            original=evidence.source_snapshot;calls=[]
            def counted(*args,**kwargs):calls.append(kwargs);return original(*args,**kwargs)
            started=time.monotonic()
            with patch.object(evidence,'source_snapshot',counted):
                if mode=='legacy':
                    # Exact previous source-only report path, with no external policy.
                    with patch.object(report,'_input_message',lambda item,render:render()):text=report.end_report(ledger)
                else:text=report.end_report(ledger)
            row=dict(language=language,repeat=repeat,mode=mode,seconds=round(time.monotonic()-started,6),
                source_snapshots=len(calls),fresh_source_reads=sum(c.get('fresh') is True for c in calls),
                source_files=len(scan.files),receipts=options.receipts,verified=text.startswith('VERIFIED'),
                five_fresh=options.receipts==5 and '5 fresh' in text,all_fresh=f'{options.receipts} fresh' in text)
            assert row['verified'] and row['all_fresh']
            assert row['source_snapshots']==(options.receipts if mode=='legacy' else 2)
            rows.append(row);print(json.dumps(row),flush=True)
summary=[dict(language=language,legacy_median_seconds=statistics.median(r['seconds'] for r in rows if r['language']==language and r['mode']=='legacy'),
              optimized_median_seconds=statistics.median(r['seconds'] for r in rows if r['language']==language and r['mode']=='optimized'))
         for language in ('python','javascript')]
value=dict(schema=1,category='source-only-human-report-controlled-ablation',model_calls=0,host_launched=False,
    project_checks_launched=False,observations=rows,summary=summary,
    limits=[f'Three local samples per mode/language on fresh 150-file inputs with {options.receipts} source receipts; order alternates by repetition.',
            'Legacy mode reproduces the prior source-only early return by overriding only the read-only report wrapper; no production source or prior artifact is changed.',
            'No external input policy or mutation engine is enabled; independent regression controls qualify closing/configuration movement and deadline handling.',
            'Component timing is not full Stop, native-model workflow speedup, application performance or coding benefit.'])
options.output.parent.mkdir(parents=True,exist_ok=True)
with options.output.open('xb') as stream:stream.write((json.dumps(value,indent=2)+'\n').encode('utf8'))
print(json.dumps(summary,indent=2))
