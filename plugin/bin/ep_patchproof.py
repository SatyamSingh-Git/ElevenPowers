"""Export exact committed patch identity and existing evidence without running checks."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.export import write
from core.patchproof.report import build, markdown


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--base', default='HEAD~1')
    parser.add_argument('--head', default='HEAD')
    parser.add_argument('--format', choices=('markdown', 'json'), default='markdown')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--require-bound', action='store_true',
                        help='gate patch/input binding only; does not certify completed work or safety')
    args = parser.parse_args()
    try:
        value = build(args.project, args.base, args.head, timeout=args.timeout)
        text = json.dumps(value, indent=2, ensure_ascii=False) + '\n' if args.format == 'json' else markdown(value)
        if args.output:
            write(args.output, text, force=args.force)
            print(f'Saved {args.output}')
        else:
            print(text, end='')
        return 1 if args.require_bound and value['binding']['state'] != 'bound' else 0
    except (ValueError, OSError) as exc:
        parser.exit(1, f'PatchProof failed: {exc}\n')


if __name__ == '__main__':
    sys.exit(main())
