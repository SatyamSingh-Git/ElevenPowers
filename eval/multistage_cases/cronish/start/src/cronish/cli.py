"""The ``cronish`` command."""
import argparse
import json
from datetime import datetime, timedelta
import sys

from . import __version__
from ._generated import TABLE_VERSION
from .describe import describe
from .errors import ScheduleError
from .expression import parse
from .fields import FIELDS
from .formatting import format_run
from .jobs import JobFileError, due_jobs, load_jobs, overlaps, upcoming
from .planner import DEFAULT_COUNT, next_runs, previous_run, runs_between
from .validate import validate

EXIT_OK = 0
EXIT_INVALID = 1
OVERLAP_HOURS = 24


def build_parser():
    parser = argparse.ArgumentParser(prog="cronish", description="Parse, explain and plan cron-style schedules.")
    parser.add_argument("--version", action="version", version=f"cronish {__version__} (name tables {TABLE_VERSION})")
    commands = parser.add_subparsers(dest="command", required=True)

    command = commands.add_parser("next", help="list the next runs of an expression")
    command.add_argument("expression")
    _add_count(command)
    _add_now(command)
    _add_json(command)

    command = commands.add_parser("last", help="show the latest run at or before now")
    command.add_argument("expression")
    _add_now(command)

    command = commands.add_parser("between", help="list every run in a window")
    command.add_argument("expression")
    command.add_argument("start", type=datetime.fromisoformat)
    command.add_argument("end", type=datetime.fromisoformat)

    command = commands.add_parser("describe", help="explain an expression in words")
    command.add_argument("expression")

    command = commands.add_parser("check", help="report what is wrong with an expression")
    command.add_argument("expression")

    command = commands.add_parser("fields", help="show the values each field selects")
    command.add_argument("expression")

    command = commands.add_parser("list", help="describe every job in a jobs file")
    command.add_argument("file")

    command = commands.add_parser("due", help="name the jobs that run this minute")
    command.add_argument("file")
    _add_now(command)

    command = commands.add_parser("upcoming", help="list the next runs across a jobs file")
    command.add_argument("file")
    _add_count(command)
    _add_now(command)
    _add_json(command)

    command = commands.add_parser("overlaps", help="list moments when jobs run together")
    command.add_argument("file")
    command.add_argument("--hours", type=int, default=OVERLAP_HOURS, help="how far ahead to look")
    _add_now(command)
    return parser


def _add_count(command):
    command.add_argument("-n", "--count", type=int, default=DEFAULT_COUNT, help="how many runs to list")


def _add_now(command):
    command.add_argument("--now", type=datetime.fromisoformat, help="plan from this ISO time instead of the clock")


def _add_json(command):
    command.add_argument("--json", action="store_true", help="print a JSON array instead of lines")


def main(argv=None, clock=datetime.now):
    args = build_parser().parse_args(argv)
    if getattr(args, "now", False) is None:
        args.now = clock()
    try:
        return COMMANDS[args.command](args)
    except (ScheduleError, JobFileError, OSError) as error:
        print(f"cronish: {error}", file=sys.stderr)
        return EXIT_INVALID


def _next(args):
    runs = next_runs(parse(args.expression), args.now, args.count)
    if args.json:
        print(json.dumps([run.isoformat() for run in runs]))
        return EXIT_OK
    for run in runs:
        print(format_run(run))
    return EXIT_OK


def _last(args):
    print(format_run(previous_run(parse(args.expression), args.now)))
    return EXIT_OK


def _between(args):
    for run in runs_between(parse(args.expression), args.start, args.end):
        print(format_run(run))
    return EXIT_OK


def _describe(args):
    print(describe(parse(args.expression)))
    return EXIT_OK


def _check(args):
    problems = validate(args.expression)
    for problem in problems:
        print(problem)
    if problems:
        return EXIT_INVALID
    print("ok")
    return EXIT_OK


def _fields(args):
    schedule = parse(args.expression)
    selected = (schedule.minutes, schedule.hours, schedule.days, schedule.months, schedule.weekdays)
    for spec, values in zip(FIELDS, selected):
        shown = "every value" if len(values) == spec.size else ", ".join(map(str, values))
        print(f"{spec.name}: {shown}")
    return EXIT_OK


def _read_jobs(path):
    with open(path, encoding="utf-8") as handle:
        return load_jobs(handle.read())


def _list(args):
    for job in _read_jobs(args.file):
        print(f"{job.name}: {describe(job.schedule)}")
    return EXIT_OK


def _due(args):
    for name in due_jobs(_read_jobs(args.file), args.now):
        print(name)
    return EXIT_OK


def _upcoming(args):
    timeline = upcoming(_read_jobs(args.file), args.now, args.count)
    if args.json:
        print(json.dumps([{"at": run.isoformat(), "job": name} for run, name in timeline]))
        return EXIT_OK
    for run, name in timeline:
        print(f"{format_run(run)} {name}")
    return EXIT_OK


def _overlaps(args):
    end = args.now + timedelta(hours=args.hours)
    for moment, names in overlaps(_read_jobs(args.file), args.now, end):
        print(f"{format_run(moment)} {', '.join(names)}")
    return EXIT_OK


COMMANDS = {
    "next": _next,
    "last": _last,
    "between": _between,
    "describe": _describe,
    "check": _check,
    "fields": _fields,
    "list": _list,
    "due": _due,
    "upcoming": _upcoming,
    "overlaps": _overlaps,
}
