"""Inspect earlier behavior evidence without running project checks."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.export import write
from core.milestones import build, markdown


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--impact', action='store_true')
    parser.add_argument('--changed', nargs='+', action='extend')
    args = parser.parse_args()
    try:
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
