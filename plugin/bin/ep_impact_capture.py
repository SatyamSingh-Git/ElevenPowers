"""Convert explicit coverage outputs; never execute project commands."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.export import write
from core.impact.coverage import convert, MAX_BYTES
from core.redact import scrub


def read(path, limit):
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('input size limit exceeded')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--kind', choices=('python', 'v8'), required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--seconds', type=float, default=30)
    args = parser.parse_args()
    try:
        value = convert(args.project, args.kind, read(args.report, MAX_BYTES),
                        json.loads(read(args.receipt, 1024*1024)), seconds=args.seconds)
        if args.output.resolve().is_relative_to(args.project.resolve()):
            relative = args.output.resolve().relative_to(args.project.resolve()).as_posix()
            if not relative.startswith('.elevenpowers/'):
                raise ValueError('project observations must be stored in .elevenpowers to preserve input identity')
        write(args.output, json.dumps(value, indent=2)+'\n', force=args.force)
        print('Saved ' + str(args.output))
        return 0 if value['complete'] else 1
    except (ValueError, OSError) as exc:
        parser.exit(2, scrub(str(exc))+'\n')


if __name__ == '__main__':
    raise SystemExit(main())
