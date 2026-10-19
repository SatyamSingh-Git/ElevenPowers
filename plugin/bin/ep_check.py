"""Run an exact project-declared check and retain its actual qualified outcome."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.checks import available, execute


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('property', nargs='?')
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--list', action='store_true', help='list configured checks without running or writing state')
    parser.add_argument('--all', action='store_true', help='run every declared property with one shared deadline and owner')
    parser.add_argument('--seconds', type=float, default=120, help='shared execution allowance, >0–600 (default 120)')
    parser.add_argument('--json', action='store_true', help='print metadata only, without captured process output')
    args = parser.parse_args()
    if sum((args.list,args.all,bool(args.property)))!=1:
        parser.error('choose one declared property, --all or --list')
    try:
        if args.all:
            from core.check_batch import execute as execute_batch
            value=execute_batch(args.project,seconds=args.seconds)
        else:
            value = available(args.project) if args.list else execute(args.project, args.property, seconds=args.seconds)
        if args.json:
            print(json.dumps(value, ensure_ascii=True, indent=2))
        elif args.list:
            print('Declared checks (profile: ' + value['profile'] + ')')
            for key, command in value['commands'].items():
                print(key + ': ' + command)
        else:
            if args.all:
                print('Declared check batch: '+value['state'])
                for issue in value['issues']:
                    print('Issue: '+issue)
            for result in value['results'] if args.all else [value]:
                print('Declared check ' + result['property'] + ': ' + result['state'])
                print('Command: ' + result['command'])
                print('Child exit: ' + str(result['exit_code']))
                print('Attempt: ' + result['attempt'])
                for issue in result['issues']:
                    print('Issue: ' + issue)
        return 0 if args.list else {'passed': 0, 'failed': 1, 'incomplete': 2}[value['state']]
    except KeyboardInterrupt:
        parser.exit(130, 'Declared check interrupted; started evidence remains incomplete.\n')
    except (ValueError, OSError):
        parser.exit(2, 'Declared check unavailable: inspect the project, configuration and allowance.\n')


if __name__ == '__main__':
    sys.exit(main())
