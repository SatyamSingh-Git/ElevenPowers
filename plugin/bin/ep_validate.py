"""Explicit native captures, matrix reports and read-only performance samples."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.export import write
from core.hosts import validation
from core.hosts.diagnostics import read_json
from core.hosts.setup import PATHS


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    capture = sub.add_parser('capture')
    capture.add_argument('host', choices=PATHS)
    capture.add_argument('--project', type=Path, required=True)
    capture.add_argument('--observe-version', action='store_true')
    capture.add_argument('--seconds', type=float, default=10)
    matrix = sub.add_parser('matrix')
    matrix.add_argument('inputs', type=Path, nargs='*')
    performance = sub.add_parser('performance')
    performance.add_argument('host', choices=PATHS)
    performance.add_argument('--project', type=Path, required=True)
    performance.add_argument('--repeats', type=int, default=3)
    performance.add_argument('--seconds', type=float, default=60)
    for command in (capture, matrix, performance):
        command.add_argument('--json', action='store_true')
        command.add_argument('--output', type=Path)
        command.add_argument('--force', action='store_true')
        command.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.force and not args.output:
            raise ValueError('--force requires --output')
        if args.operation == 'capture':
            value = validation.capture(args.host, args.project, args.seconds, args.observe_version)
            passed = value['state'] == 'passed'
        elif args.operation == 'matrix':
            if len(args.inputs) > 100:
                raise ValueError('at most 100 capture files')
            value = validation.matrix([read_json(p) for p in args.inputs])
            passed = value['passed'] == value['total']
        else:
            from core.hosts.performance import measure
            value = measure(args.host, args.project, args.repeats, args.seconds)
            passed = value['state'] == 'complete'
        if args.json:
            rendered = json.dumps(value, indent=2, allow_nan=False) + '\n'
        elif args.operation == 'performance':
            from core.hosts.performance import render
            rendered = render(value)
        else:
            rendered = validation.render(value)
        if args.output:
            write(args.output, rendered, force=args.force)
        else:
            print(rendered, end='')
        return 1 if args.check and not passed else 0
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    sys.exit(main())
