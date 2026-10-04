"""Explain possible impact from fresh source and qualified project relationships."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.export import write
from core.impact import analyze, build, markdown
from core.redact import scrub


def main():
    # Redirected Windows terminals may default to a legacy code page. JSON and
    # paths/labels retain Unicode consistently for both humans and API readers.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*', help='relative file paths or declared node IDs')
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--graph', action='store_true', help='export the graph instead of querying')
    parser.add_argument('--observations', type=Path)
    parser.add_argument('--history', type=int, default=0)
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--max-files', type=int)
    parser.add_argument('--max-bytes', type=int)
    parser.add_argument('--max-depth', type=int, default=6)
    parser.add_argument('--max-results', type=int, default=100)
    parser.add_argument('--change', default='')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.graph and args.files:
        parser.error('--graph cannot be combined with query files')
    if not args.graph and not args.files:
        parser.error('provide query files/node IDs, or --graph')
    if args.force and not args.output:
        parser.error('--force requires --output')
    try:
        value = build(args.project, seconds=args.seconds, max_files=args.max_files,
                      max_bytes=args.max_bytes, observations=args.observations, history=args.history)
        if args.graph:
            report = value.to_dict()
            output = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
        else:
            report = analyze(value, args.files, max_depth=args.max_depth, max_results=args.max_results)
            if args.change:
                report['change'] = scrub(args.change)
            output = json.dumps(report, indent=2, ensure_ascii=False) + '\n' if args.json else markdown(report)
        if args.output:
            write(args.output, output, force=args.force)
            print(f'Saved {args.output}')
        else:
            print(output, end='')
        return 1 if args.check and not report['coverage']['complete'] else 0
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Impact query failed: {scrub(str(exc))}\n')


if __name__ == '__main__':
    sys.exit(main())
