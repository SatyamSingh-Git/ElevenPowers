"""Which functions do the tests reach, and does emptying one fail any of them? Report only."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.testminer.observe import OBSERVED, record
from core.testminer.runner import describe, mine


def record_main(argv):
    parser = argparse.ArgumentParser(prog='ep_testminer.py record',
                                     description='Run your program once under coverage.py and keep which lines ran.')
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('command', nargs=argparse.REMAINDER, help='-- python app.py ARGS, or -- python -m MODULE ARGS')
    args = parser.parse_args(argv)
    words = args.command[1:] if args.command[:1] == ['--'] else args.command
    try:
        status, observation = record(args.project, words)
    except (OSError, ValueError) as exc:
        parser.exit(2, f'TestMiner could not record: {exc}\n')
    if observation is None:
        print(f'No file of this project ran under coverage.py (the command exited {status}); nothing recorded, '
              'and the previous record, if any, is kept. A package imported from an installed copy is measured '
              'there, not here.')
    else:
        lines = sum(len(item['lines']) for item in observation['files'].values())
        print(f"Recorded {lines} lines in {len(observation['files'])} files to {OBSERVED}")
    return status


def main():
    if sys.argv[1:2] == ['record']:
        return record_main(sys.argv[2:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--base', default='', help='examine the functions changed since this commit')
    parser.add_argument('--function', action='append', default=[], metavar='FILE::NAME',
                        help='examine one function, e.g. svc.py::Box.size (repeatable)')
    parser.add_argument('--path', action='append', default=[], metavar='FILE',
                        help='examine every function in a file (repeatable)')
    parser.add_argument('--observed', action='store_true',
                        help='examine the functions a run saved by "ep_testminer.py record" executed')
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
                      test_seconds=args.test_seconds, observed=args.observed)
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
        print(describe(item))
    if checked and not args.all:
        print(f"{len(checked)} function{'s' if len(checked) > 1 else ''} checked by "
              f"{'their' if len(checked) > 1 else 'its'} tests (--all lists them)")
    if skipped:
        print(f'{len(skipped)} more functions not examined (budget); raise --limit or --seconds, or see --json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
