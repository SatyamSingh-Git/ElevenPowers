"""Check that the runtime is actually seeing what its host sends.

    ep-doctor [--cwd DIR] [--host]

`--host` additionally drives the launcher as a process with a payload on its
stdin — success, failure and stop — rather than calling the reader in this one.
Unrecognised flags are refused rather than ignored: this script used to accept
`--host` silently and print six green lines about something else entirely, which
is a passing check that means nothing.

Exits non-zero when something is wrong, so it works in continuous integration
as well as by hand.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.doctor import report  # noqa: E402


def main(argv: list[str]) -> int:
    from core.hosts.setup import PATHS
    parser = argparse.ArgumentParser(description='Check runtime configuration or explicitly prepare/inspect native acceptance.')
    parser.add_argument('--cwd')
    parser.add_argument('--host', action='store_true', help='Run the Claude launcher replay diagnostics')
    parser.add_argument('--platform', choices=PATHS)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--prepare-acceptance', metavar='NEW_DIR')
    modes.add_argument('--acceptance', metavar='DIR')
    parser.add_argument('--language', choices=('python', 'javascript'))
    parser.add_argument('--host-version', help='Explicit operator version metadata; does not authenticate the host')
    parser.add_argument('--advice', action='store_true', help='Explicitly enable bounded advice in a new acceptance exercise')
    parser.add_argument('--seconds', type=float, help='Cooperative acceptance read budget, default 10 seconds')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv[1:])
    exercise = args.prepare_acceptance or args.acceptance
    if args.host and (args.platform or exercise):
        parser.error('--host is the Claude launcher replay; choose it independently of --platform/acceptance')
    if exercise and (not args.platform or args.cwd):
        parser.error('acceptance requires --platform and its explicit directory; omit --cwd')
    if (args.language is not None or args.host_version is not None) and not args.prepare_acceptance:
        parser.error('--language and --host-version apply only to --prepare-acceptance')
    if args.seconds is not None and not args.acceptance:
        parser.error('--seconds applies only to --acceptance')
    if args.advice and not args.prepare_acceptance:
        parser.error('--advice applies only to --prepare-acceptance')
    try:
        if args.prepare_acceptance:
            from core.hosts.acceptance import prepare
            value = prepare(args.platform, args.prepare_acceptance, args.language or 'python',
                            Path(__file__).resolve().parents[2], version=args.host_version or '', advice=args.advice)
            print(json.dumps(value, indent=2) if args.json else
                  f"Prepared {value['host']} / {value['language']} exercise: {value['project']}\n"
                  f"Instructions: {value['instructions']}\nNative acceptance: waiting; no host was launched.")
            return 0
        if args.acceptance:
            from core.hosts.acceptance import inspect, render
            value = inspect(args.platform, args.acceptance, timeout=10 if args.seconds is None else args.seconds)
            print(json.dumps(value, indent=2) if args.json else render(value))
            return 0 if value['state'] == 'passed' else 1
        where = Path(args.cwd or '.').resolve()
        if args.platform:
            from core.hosts.doctor import report as native_report
            body, ok = native_report(args.platform, where)
        else:
            body, ok = report(where, host=args.host)
        print(json.dumps({'ok': ok, 'report': body}, indent=2) if args.json else body)
        return 0 if ok else 1
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
