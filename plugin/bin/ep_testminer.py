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
    parser.add_argument('--all', action='store_true', help='also list the functions their tests check')
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
    skipped = [item for item in result['functions'] if item['reason'] == 'budget']
    checked = [item for item in result['functions'] if item['verdict'] == 'checked']
    for item in result['functions']:
        if item['reason'] == 'budget' or (item['verdict'] == 'checked' and not args.all):
            continue
        detail = item['reason'] or (', '.join(item['tests']) if item['verdict'] == 'reached, not checked' else '')
        print(f"{item['path']}:{item['line']} {item['name']}: {item['verdict']}" + (f' ({detail})' if detail else ''))
    if checked and not args.all:
        print(f"{len(checked)} function{'s' if len(checked) > 1 else ''} checked by "
              f"{'their' if len(checked) > 1 else 'its'} tests (--all lists them)")
    if skipped:
        print(f'{len(skipped)} more functions not examined (budget); raise --limit or --seconds, or see --json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
