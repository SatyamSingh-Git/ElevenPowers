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
    args = parser.parse_args()
    try:
        if args.json:
            value = inspect(args.host, args.project)
            print(json.dumps(value, indent=2))
        else:
            print(report(args.host, args.project))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Readiness failed: {exc}\n')


if __name__ == '__main__':
    main()
