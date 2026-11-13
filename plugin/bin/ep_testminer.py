"""Which functions do the tests reach, and does emptying one fail any of them? Report only."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.testminer.runner import mine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--base', default='', help='examine the functions changed since this commit')
    parser.add_argument('--function', action='append', default=[], metavar='FILE::NAME',
                        help='examine one function, e.g. svc.py::Box.size (repeatable)')
    parser.add_argument('--path', action='append', default=[], metavar='FILE',
                        help='examine every function in a file (repeatable)')
    parser.add_argument('--command', default='', help="the test command (default: the project's tests command)")
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--test-seconds', type=float, default=15)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        result = mine(args.project, base=args.base, names=tuple(args.function), paths=tuple(args.path),
                      command=args.command, seconds=args.seconds, limit=args.limit,
                      test_seconds=args.test_seconds)
    except (OSError, ValueError) as exc:
        parser.exit(2, f'TestMiner could not run: {exc}\n')
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    for issue in result['issues']:
        print('Issue: ' + issue)
    for item in result['functions']:
        detail = item['reason'] or (', '.join(item['tests']) if item['verdict'] == 'reached, not checked' else '')
        print(f"{item['path']}:{item['line']} {item['name']}: {item['verdict']}" + (f' ({detail})' if detail else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
