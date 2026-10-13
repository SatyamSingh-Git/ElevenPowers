"""Explicit local approval for project-declared external input roots."""
import sys
sys.dont_write_bytecode = True

import argparse
import json
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from core.inputs.bindings import bind
from core.redact import scrub_values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action',required=True)
    approval = commands.add_parser('bind',help='explicitly approve one declared local root')
    approval.add_argument('--project',type=Path,default=Path.cwd())
    approval.add_argument('--name',required=True)
    approval.add_argument('--path',type=Path,required=True)
    approval.add_argument('--replace',action='store_true')
    args = parser.parse_args()
    try:
        bind(args.project,args.name,args.path,replace=args.replace)
        print(json.dumps(scrub_values({'root':args.name,'state':'bound'}),ensure_ascii=True))
        return 0
    except (ValueError,OSError,TimeoutError) as error:
        parser.exit(2,'Input approval unavailable: '+type(error).__name__+'; inspect declaration and local root.\n')


if __name__ == '__main__':
    sys.exit(main())
