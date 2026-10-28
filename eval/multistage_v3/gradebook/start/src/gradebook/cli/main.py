"""Command line entry point: `gradebook <command> ...`.

Each subcommand is handled by the function `cmd_<command>` in `commands`,
with dashes in the command name written as underscores.
"""
import argparse
import sys

from ..errors import GradebookError
from . import commands

DEFAULT_BOOK = "gradebook.json"
EXIT_ERROR = 1
DEFAULT_AT_RISK = 70.0


def build_parser():
    parser = argparse.ArgumentParser(prog="gradebook", description="Keep a course gradebook.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-course", help="write a starter course file to edit")
    init.add_argument("out")
    init.add_argument("--code", required=True)
    init.add_argument("--title", required=True)

    new = sub.add_parser("new", help="start a gradebook from a course file")
    new.add_argument("course_file")
    _book_option(new)

    course = sub.add_parser("course", help="the course outline")
    _format_option(course)
    _book_option(course)

    imported = sub.add_parser("import", help="import a roster, score file, LMS export or score sheet")
    imported.add_argument("kind", help="roster, scores, lms or sheet")
    imported.add_argument("file")
    _book_option(imported)

    roster = sub.add_parser("roster", help="list the students")
    _book_option(roster)

    sync = sub.add_parser("sync-roster", help="add new students from the office's roster file")
    sync.add_argument("file")
    _book_option(sync)

    drop = sub.add_parser("drop-student", help="take a student and their scores off the roster")
    drop.add_argument("student")
    _book_option(drop)

    merge = sub.add_parser("merge", help="merge another section's gradebook into this one")
    merge.add_argument("other")
    _book_option(merge)

    score = sub.add_parser("score", help="record one score")
    score.add_argument("student")
    score.add_argument("assignment")
    score.add_argument("points", help="points earned, or EX to excuse the assignment")
    score.add_argument("--day", type=int, help="term day the work was handed in")
    _book_option(score)

    curve = sub.add_parser("curve", help="curve one assignment")
    curve.add_argument("assignment")
    how = curve.add_mutually_exclusive_group(required=True)
    how.add_argument("--add", type=float, help="add this many points to every score")
    how.add_argument("--top", type=float, help="scale scores so the highest becomes this many points")
    _book_option(curve)

    report = sub.add_parser("report", help="the class report")
    _format_option(report)
    _as_of_option(report)
    _book_option(report)

    what_if = sub.add_parser("what-if", help="the class's grades under different category weights")
    what_if.add_argument("--weights", required=True, help="for example homework=30,quizzes=30,exams=40")
    _format_option(what_if)
    _as_of_option(what_if)
    _book_option(what_if)

    categories = sub.add_parser("categories", help="the class's standing in each category")
    _format_option(categories)
    _as_of_option(categories)
    _book_option(categories)

    assignments = sub.add_parser("assignments", help="how the class did on each assignment")
    _format_option(assignments)
    _as_of_option(assignments)
    _book_option(assignments)

    missing = sub.add_parser("missing", help="work that is due and not handed in")
    missing.add_argument("--as-of", type=int, dest="as_of", required=True, help="term day")
    _format_option(missing)
    _book_option(missing)

    risk = sub.add_parser("at-risk", help="students below a percent")
    risk.add_argument("--as-of", type=int, dest="as_of", required=True, help="term day")
    risk.add_argument("--below", type=float, default=DEFAULT_AT_RISK,
                      help=f"percent to flag students under (default {DEFAULT_AT_RISK:g})")
    _format_option(risk)
    _book_option(risk)

    late = sub.add_parser("late", help="late submissions and their penalties")
    _format_option(late)
    _book_option(late)

    progress = sub.add_parser("progress", help="one student's progress report")
    progress.add_argument("student")
    _as_of_option(progress)
    _book_option(progress)

    explain = sub.add_parser("explain", help="how a student's course grade is reached")
    explain.add_argument("student")
    _as_of_option(explain)
    _book_option(explain)

    cards = sub.add_parser("report-cards", help="write one report card per student into a folder")
    cards.add_argument("folder")
    _as_of_option(cards)
    _book_option(cards)

    forecast = sub.add_parser("forecast", help="what a student needs to finish with a letter")
    forecast.add_argument("student")
    forecast.add_argument("letter")
    forecast.add_argument("--as-of", type=int, dest="as_of", required=True, help="term day")
    _book_option(forecast)

    sheet = sub.add_parser("sheet", help="write a score sheet to fill in by hand")
    sheet.add_argument("out")
    _book_option(sheet)

    export = sub.add_parser("export-grades", help="write the term grades file")
    export.add_argument("out")
    _as_of_option(export)
    _book_option(export)

    scores = sub.add_parser("export-scores", help="write every recorded score as a score file")
    scores.add_argument("out")
    _book_option(scores)

    archive = sub.add_parser("archive", help="bundle the term's gradebook, scores and grades in a zip file")
    archive.add_argument("out")
    _book_option(archive)

    check = sub.add_parser("check", help="look for problems in a hand-edited gradebook file")
    _book_option(check)

    day = sub.add_parser("day", help="the term day a date falls on")
    day.add_argument("date", help="YYYY-MM-DD")
    day.add_argument("--calendar", required=True, help="term calendar file")

    when = sub.add_parser("date", help="the date a term day falls on")
    when.add_argument("day", type=int)
    when.add_argument("--calendar", required=True, help="term calendar file")

    transcript = sub.add_parser("transcript", help="a student's transcript from posted grades files")
    transcript.add_argument("student")
    transcript.add_argument("files", nargs="+")
    return parser



def _book_option(parser):
    parser.add_argument("--book", default=DEFAULT_BOOK, help=f"gradebook file (default {DEFAULT_BOOK})")


def _format_option(parser):
    parser.add_argument("--format", default="text", help="text, csv or markdown (default text)")


def _as_of_option(parser):
    parser.add_argument("--as-of", type=int, dest="as_of",
                        help="grade as of this term day (default: every assignment counts)")


def main(argv=None):
    args = build_parser().parse_args(argv)
    handler = getattr(commands, "cmd_" + args.command.replace("-", "_"))
    try:
        return handler(args, sys.stdout)
    except GradebookError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
