"""Install/remove project hooks without changing host trust or other hooks."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.hosts.bridge import PLATFORMS
from core.hosts.setup import install, remove


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", choices=PLATFORMS)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()
    try:
        path = remove(args.platform, args.project) if args.remove else install(
            args.platform, args.project, sys.executable, Path(__file__).resolve().parents[2])
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Setup failed: {exc}\n")
    print(f"Updated {path}")
    if not args.remove:
        print("Enable/review these hooks in your host, then restart the project session.")


if __name__ == "__main__":
    main()
