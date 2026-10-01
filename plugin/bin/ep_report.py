"""Export a local verification report without executing project commands."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.export import build, markdown, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--format', choices=('markdown', 'json'), default='markdown')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--require-verified', action='store_true')
    args = parser.parse_args()
    try:
        value = build(args.project, timeout=args.timeout)
        text = json.dumps(value, indent=2, ensure_ascii=False) + '\n' if args.format == 'json' else markdown(value)
        if args.output:
            write(args.output, text, force=args.force)
            print(f'Saved {args.output}')
        else:
            print(text, end='')
        return 1 if args.require_verified and value['state'] != 'VERIFIED' else 0
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Report failed: {exc}\n')


if __name__ == '__main__':
    sys.exit(main())
