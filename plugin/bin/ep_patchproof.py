"""Report or plan committed-patch evidence; explicitly verify declared commands."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.export import write
from core.patchproof.report import build, markdown
from core.patchproof.planning import plan, markdown as plan_markdown
from core.patchproof.execution import verify


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--base', default='HEAD~1')
    parser.add_argument('--head', default='HEAD')
    parser.add_argument('--format', choices=('markdown', 'json'), default='markdown')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--timeout', type=float, default=120)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true', help='read-only required command plan')
    mode.add_argument('--verify', action='store_true', help='explicitly execute project-declared checks')
    parser.add_argument('--seconds', type=float, default=120, help='shared plan/execution allowance, 0–600')
    parser.add_argument('--command-seconds', type=float, default=30, help='per-command allowance, >0–300')
    parser.add_argument('--rerun', action='store_true', help='run all declared checks instead of reusing local results')
    parser.add_argument('--impact', action='store_true',
                        help='include optional fresh impact recommendations; runs no checks')
    parser.add_argument('--require-bound', action='store_true',
                        help='gate patch/input binding only; does not certify completed work or safety')
    args = parser.parse_args()
    if args.rerun and not (args.plan or args.verify):
        parser.error('--rerun requires --plan or --verify')
    try:
        if args.output and args.output.exists() and not args.force:
            raise ValueError('output already exists; use --force to overwrite')
        if args.plan or args.verify:
            function = verify if args.verify else plan
            value = function(args.project, args.base, args.head, seconds=args.seconds,
                             command_seconds=args.command_seconds, impact=args.impact, reuse=not args.rerun)
            if args.verify:
                from core.patchproof.execution import markdown as execution_markdown
                rendered = execution_markdown(value)
            else:
                rendered = plan_markdown(value)
        else:
            value = build(args.project, args.base, args.head, timeout=args.timeout, impact=args.impact)
            rendered = markdown(value)
        text = json.dumps(value, indent=2, ensure_ascii=False) + '\n' if args.format == 'json' else rendered
        if args.output:
            write(args.output, text, force=args.force)
            print(f'Saved {args.output}')
        else:
            print(text, end='')
        if args.verify:
            return {'passed': 0, 'failed': 1, 'incomplete': 2}[value['state']]
        bundle = value['bundle'] if args.plan else value
        return 1 if args.require_bound and bundle['binding']['state'] != 'bound' else 0
    except KeyboardInterrupt:
        parser.exit(130, 'PatchProof interrupted; started attempts remain incomplete.\n')
    except (ValueError, OSError) as exc:
        parser.exit(1, f'PatchProof failed: {exc}\n')


if __name__ == '__main__':
    sys.exit(main())
