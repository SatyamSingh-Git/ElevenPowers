"""Inspect earlier behavior evidence without running project checks."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.export import write
from core.milestones import build, markdown


def main():
    # Proposals quote a project's own words, which a Windows pipe's code page cannot always encode.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--impact', action='store_true')
    parser.add_argument('--changed', nargs='+', action='extend')
    parser.add_argument('--propose', action='store_true',
                        help='propose files that carry the same rule, for a person to certify as milestones')
    parser.add_argument('--limit', type=int, default=50, help='with --propose: how many pairs to list')
    parser.add_argument('--marked', action='store_true',
                        help='list the rules marked in the code with LINT.IfChange / LINT.ThenChange')
    args = parser.parse_args()
    try:
        if args.marked:
            from core.milestones.marked import listing, listing_text
            value = listing(args.project)
            text = json.dumps(value, indent=2, ensure_ascii=False) + '\n' if args.json else listing_text(value)
            if args.output:
                write(args.output, text, force=args.force)
                print(f'Saved {args.output}')
            else:
                print(text, end='')
            return 0
        if args.propose:
            from core.milestones.propose import markdown as proposal_text, propose
            value = propose(args.project, limit=args.limit, seconds=args.seconds)
            text = json.dumps(value, indent=2, ensure_ascii=False) + '\n' if args.json else proposal_text(value)
            if args.output:
                write(args.output, text, force=args.force)
                print(f'Saved {args.output}')
            else:
                print(text, end='')
            return 0
        value = build(args.project, seconds=args.seconds, impact=args.impact, changed=args.changed)
        text = json.dumps(value, indent=2, ensure_ascii=False) + '\n' if args.json else markdown(value)
        if args.output:
            write(args.output, text, force=args.force)
            print(f'Saved {args.output}')
        else:
            print(text, end='')
        return 1 if args.check and value['state'] != 'CURRENT' else 0
    except (OSError, ValueError) as error:
        parser.exit(2, f'Milestone report failed: {error}\n')


if __name__ == '__main__':
    sys.exit(main())
