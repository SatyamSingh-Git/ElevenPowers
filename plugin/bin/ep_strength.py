"""Run optional, report-only changed-code test-strength analysis."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core import jobs
from core.export import _portable
from core.ledger import Ledger
from core.strength.runner import analyze
from core.strength.settings import settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--base', help='explicit full Git base commit (otherwise recorded task base)')
    parser.add_argument('--command', help='focused test command, run in the private copy')
    parser.add_argument('--seconds', type=float)
    parser.add_argument('--max-mutants', type=int)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError('project must be a directory')
        ledger = Ledger.load(root)
        raw = dict(ledger.config.strength)
        if args.seconds is not None:
            raw['seconds'] = args.seconds
        if args.max_mutants is not None:
            raw['max_mutants'] = args.max_mutants
        settings(raw)
        ledger._config = replace(ledger.config, strength=raw)
        value = _portable(analyze(ledger, base=args.base, command=args.command), root)
        if args.json:
            print(json.dumps(value, indent=2, allow_nan=False))
        else:
            print('Test strength: ' + value['state'] + ' (informational)')
            print('Baseline: ' + value['baseline'] + '; attempts: ' + str(value['attempts']))
            print(', '.join(f'{name}: {count}' for name, count in value['summary'].items()))
            for issue in value['issues']:
                print('- ' + issue)
            print(value['limitations'][0])
        return 0 if value['state'] in ('complete', 'not_applicable', 'disabled') else 2
    except (OSError, ValueError, jobs.Busy, jobs.Superseded) as exc:
        parser.exit(2, f'Test strength could not run: {exc}\n')


if __name__ == '__main__':
    sys.exit(main())
