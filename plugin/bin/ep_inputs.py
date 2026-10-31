"""Explicit local approval for project-declared external input roots and remote resources."""
import sys
sys.dont_write_bytecode = True

import argparse
import json
import math
from pathlib import Path
import subprocess
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from core.inputs.bindings import bind
from core.inputs.collection import capture
from core.inputs import remote
from core.jobs import Busy
from core.redact import scrub_values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action',required=True)
    approval = commands.add_parser('bind',help='explicitly approve one declared local root')
    approval.add_argument('--project',type=Path,default=Path.cwd())
    approval.add_argument('--name',required=True)
    approval.add_argument('--path',type=Path,required=True)
    approval.add_argument('--replace',action='store_true')
    inspection = commands.add_parser('inspect',help='read fresh declared inputs without running commands')
    inspection.add_argument('--project',type=Path,default=Path.cwd())
    inspection.add_argument('--seconds',type=float,default=10)
    inspection.add_argument('--check',action='store_true')
    remote_approval = commands.add_parser('approve-remote',help='explicitly approve one declared remote URL')
    remote_approval.add_argument('--project',type=Path,default=Path.cwd())
    remote_approval.add_argument('--name',required=True)
    observation = commands.add_parser('observe',help='fetch approved declared remotes now and record them')
    observation.add_argument('--project',type=Path,default=Path.cwd())
    observation.add_argument('--name',action='append')
    observation.add_argument('--seconds',type=float)
    observation.add_argument('--check',action='store_true')
    listing = commands.add_parser('remotes',help='summarise recorded remote observations without network access')
    listing.add_argument('--project',type=Path,default=Path.cwd())
    args = parser.parse_args()
    try:
        if args.action == 'approve-remote':
            print(json.dumps(remote.approve(args.project,args.name),ensure_ascii=True))
            return 0
        if args.action == 'observe':
            rows = scrub_values(remote.observe(args.project,args.name,seconds=args.seconds))
            print(json.dumps(rows,ensure_ascii=True))
            return 1 if args.check and any(r['state'] != 'complete' for r in rows) else 0
        if args.action == 'remotes':
            value = remote.status(args.project)
            value.pop('_rows',None)
            print(json.dumps(scrub_values(value),ensure_ascii=True))
            return 0
        if args.action == 'inspect':
            if not math.isfinite(args.seconds) or not 0 <= args.seconds <= 60:
                raise ValueError('inspection seconds outside finite range')
            value = capture(args.project,time.monotonic()+args.seconds)
            print(json.dumps(value,ensure_ascii=True))
            return 1 if args.check and value['state'] != 'available' else 0
        bind(args.project,args.name,args.path,replace=args.replace)
        print(json.dumps(scrub_values({'root':args.name,'state':'bound'}),ensure_ascii=True))
        return 0
    except (ValueError,OSError,TimeoutError,Busy,subprocess.SubprocessError) as error:
        parser.exit(2,'Input approval unavailable: '+type(error).__name__+'; inspect declaration and local root.\n')


if __name__ == '__main__':
    sys.exit(main())
