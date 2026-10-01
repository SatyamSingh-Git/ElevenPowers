"""Read-only project readiness: ep_ready.py HOST --project DIR [--json]."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.hosts.onboarding import HOSTS, inspect, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', choices=HOSTS)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--check', action='store_true', help='exit nonzero unless required pipeline stages are observed')
    args = parser.parse_args()
    try:
        value = inspect(args.host, args.project, args.seconds)
        if args.json:
            print(json.dumps(value, indent=2))
        else:
            from core.health import render
            print(render(value))
        return 1 if args.check and value['health']['state'] != 'observed' else 0
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Readiness failed: {exc}\n')


if __name__ == '__main__':
    sys.exit(main())
