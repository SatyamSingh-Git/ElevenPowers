#!/usr/bin/env python3
"""Explicitly check one project-declared OpenAPI contract and retain its receipt."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.export import _portable, _text, write
from core.patchproof.openapi import check


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='.')
    parser.add_argument('--id', required=True, help='ID in elevenpowers.contracts.json')
    parser.add_argument('--engine', required=True, help='explicit trusted oasdiff 1.33.0 executable')
    parser.add_argument('--base', default='HEAD~1')
    parser.add_argument('--head', default='HEAD')
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--format', choices=['json', 'markdown'], default='markdown')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        root = Path(args.project).resolve(strict=True)
        row = check(root, args.id, args.engine, args.base, args.head, seconds=args.seconds)
        public = {**row, 'producer': {k: v for k, v in row['producer'].items() if k != 'executable'}}
        public = _portable(public, root)
        text = json.dumps(public, indent=2, ensure_ascii=False) + '\n' if args.format == 'json' else (
            '# ElevenPowers OpenAPI contract observation\n\n' +
            '\n'.join('- ' + _text(key) + ': ' + _text(value) for key, value in public.items()) +
            '\n\nUnsigned standalone-spec observation. Export PatchProof to inspect current freshness and patch association.\n')
        if args.output:
            write(args.output, text, force=args.force)
        else:
            print(text, end='')
        return (0 if row['result'] == 'pass' else 1) if row['execution'] == 'complete' else 2
    except (OSError, ValueError, TypeError):
        print('Contract observation or publication unavailable; inspect declared inputs, engine and retained state.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
