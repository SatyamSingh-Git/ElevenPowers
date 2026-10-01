"""Install/remove project hooks without changing host trust or other hooks."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.hosts.onboarding import HOSTS, select_host, report
from core.hosts.setup import install, remove


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", nargs='?', default='auto', choices=('auto', *HOSTS))
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()
    try:
        args.platform = select_host(args.platform, args.project)
        path = remove(args.platform, args.project) if args.remove else install(
            args.platform, args.project, sys.executable, Path(__file__).resolve().parents[2])
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Setup failed: {exc}\n")
    print(f"Updated {path}")
    if not args.remove:
        print(report(args.platform, args.project))


if __name__ == "__main__":
    main()
