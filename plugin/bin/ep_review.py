"""Is this change pinned by its tests? Runs the declared test command in a private worktree.

Report only: exit 0 whenever a report is produced, whatever the verdict.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.export import _portable, write
from core.review import TIMEOUT, markdown, review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--base', required=True, help='the commit the change starts from')
    parser.add_argument('--head', default='HEAD', help='the commit with the change (default HEAD)')
    parser.add_argument('--command', help="test command to judge (default: the project's declared tests command)")
    parser.add_argument('--timeout', type=float, default=TIMEOUT, help='seconds per run')
    parser.add_argument('--format', choices=('markdown', 'json'), default='markdown')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        root = args.project.resolve(strict=True)
        value = _portable(review(root, args.base, args.head, command=args.command, timeout=args.timeout), root)
        text = json.dumps(value, indent=2, ensure_ascii=False) + '\n' if args.format == 'json' else markdown(value)
        if args.output:
            write(args.output, text, force=args.force)
            print(f'Saved {args.output}')
        else:
            print(text, end='')
        return 0
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Review failed: {exc}\n')


if __name__ == '__main__':
    sys.exit(main())
