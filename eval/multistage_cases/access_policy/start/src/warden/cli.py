"""`python -m warden check|lint|report ...`"""
import argparse
import sys

from .audit import explain, write_log
from .errors import PolicyError
from .evaluator import Evaluator
from .lint import lint
from .loader import load_file
from .model import Request, User
from .report import TOP, format_summary, summarize_file


def _pairs(items):
    pairs = {}
    for item in items:
        key, sep, value = item.partition("=")
        if not sep:
            raise PolicyError(f"expected key=value: {item}")
        pairs[key] = value
    return pairs


def _check(args):
    user = User(args.user, tuple(args.role), _pairs(args.user_attr))
    decision = Evaluator(load_file(args.policy)).decide(
        Request(user, args.action, args.resource, _pairs(args.resource_attr)))
    print(explain(decision))
    if args.log:
        write_log([decision], args.log)
    return 0 if decision.allowed else 1


def _lint(args):
    findings = lint(load_file(args.policy))
    for finding in findings:
        print(finding)
    return 1 if findings else 0


def _report(args):
    print(format_summary(summarize_file(args.log), top=args.top))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="warden")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check", help="decide one request and explain the answer")
    check.add_argument("policy")
    check.add_argument("user")
    check.add_argument("action")
    check.add_argument("resource")
    check.add_argument("--role", action="append", default=[])
    check.add_argument("--user-attr", action="append", default=[], metavar="KEY=VALUE")
    check.add_argument("--resource-attr", action="append", default=[], metavar="KEY=VALUE")
    check.add_argument("--log", help="append the decision to this audit log")
    check.set_defaults(run=_check)

    lint_command = commands.add_parser("lint", help="warn about rules and roles that look wrong")
    lint_command.add_argument("policy")
    lint_command.set_defaults(run=_lint)

    report = commands.add_parser("report", help="summarize an audit log")
    report.add_argument("log")
    report.add_argument("--top", type=int, default=TOP)
    report.set_defaults(run=_report)

    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except PolicyError as error:
        print(f"warden: {error}", file=sys.stderr)
        return 2
