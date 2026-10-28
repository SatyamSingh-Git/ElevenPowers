"""What each `gradebook` subcommand does. Each returns the process exit code."""
from datetime import date
from pathlib import Path

from ..errors import ConfigError, ImportFailed
from ..grading.explain import explain_grade
from ..model.calendar import load_calendar
from ..reports.assignments import assignment_report
from ..reports.attention import at_risk, missing_work
from ..reports.categories import category_report
from ..reports.course_outline import course_outline
from ..reports.formatting import render
from ..reports.late_work import late_work
from ..reports.progress import progress_report, render_progress
from ..reports.report_cards import write_report_cards
from ..reports.score_sheet import write_score_sheet
from ..reports.summary import class_summary
from ..services.checks import check_gradebook
from ..services.curve import curve_assignment
from ..services.forecast import describe, forecast
from ..services.gradebook import Gradebook
from ..services.merge import merge_sections
from ..services.roster_sync import describe_changes, sync_roster
from ..services.transcript import build_transcript, render_transcript
from ..services.what_if import parse_weights, what_if
from ..storage.archive import archive_term
from ..storage.course_config import load_course
from ..storage.course_template import write_starter_course
from ..storage.csv_util import EXCUSED
from ..storage.grades_csv import export_grades
from ..storage.gradebook_file import load_gradebook, save_gradebook
from ..storage.scores_export import export_scores

EXIT_PROBLEMS = 3


def cmd_init_course(args, out):
    path = write_starter_course(args.out, args.code, args.title)
    print(f"Wrote a starter course file to {path}; edit it, then run `gradebook new {path}`", file=out)
    return 0


def cmd_new(args, out):
    if Path(args.book).exists():
        raise ConfigError(f"{args.book} already exists")
    course = load_course(args.course_file)
    save_gradebook(Gradebook(course), args.book)
    print(f"Started {args.book} for {course.code} {course.title}", file=out)
    return 0


def cmd_course(args, out):
    book = load_gradebook(args.book)
    out.write(render(course_outline(book.course), args.format))
    return 0


def cmd_import(args, out):
    book = load_gradebook(args.book)
    summary = book.import_file(args.kind, args.file)
    save_gradebook(book, args.book)
    print(f"Imported {summary.recorded} {summary.kind} entries from {Path(args.file).name}"
          f" ({summary.rows} rows, {summary.skipped} skipped)", file=out)
    return 0


def cmd_roster(args, out):
    book = load_gradebook(args.book)
    for student in sorted(book.students, key=lambda s: s.sort_key()):
        print(f"{student.student_id}  {student.sort_name}", file=out)
    return 0


def cmd_sync_roster(args, out):
    book = load_gradebook(args.book)
    changes = sync_roster(book, Path(args.file))
    save_gradebook(book, args.book)
    for line in describe_changes(changes):
        print(line, file=out)
    return 0


def cmd_drop_student(args, out):
    book = load_gradebook(args.book)
    name = book.student(args.student).display_name
    book.remove_student(args.student)
    save_gradebook(book, args.book)
    print(f"Dropped {name} ({args.student})", file=out)
    return 0


def cmd_merge(args, out):
    book = load_gradebook(args.book)
    added = merge_sections(book, load_gradebook(args.other))
    save_gradebook(book, args.book)
    print(f"Merged {added} students from {args.other}", file=out)
    return 0


def cmd_score(args, out):
    book = load_gradebook(args.book)
    if args.points == EXCUSED:
        book.excuse(args.student, args.assignment)
        print(f"Excused {args.student} from {args.assignment}", file=out)
    else:
        try:
            points = float(args.points)
        except ValueError:
            raise ImportFailed(f"cannot read points {args.points}") from None
        book.record_score(args.student, args.assignment, points, args.day)
        print(f"Recorded {points:g} for {args.student} on {args.assignment}", file=out)
    save_gradebook(book, args.book)
    return 0


def cmd_curve(args, out):
    book = load_gradebook(args.book)
    changed = curve_assignment(book, args.assignment, add=args.add, top=args.top)
    save_gradebook(book, args.book)
    print(f"Curved {changed} scores on {args.assignment}", file=out)
    return 0


def cmd_report(args, out):
    book = load_gradebook(args.book)
    out.write(render(class_summary(book, args.as_of), args.format))
    return 0


def cmd_what_if(args, out):
    book = load_gradebook(args.book)
    out.write(render(what_if(book, parse_weights(args.weights), args.as_of), args.format))
    return 0


def cmd_categories(args, out):
    book = load_gradebook(args.book)
    out.write(render(category_report(book, args.as_of), args.format))
    return 0


def cmd_assignments(args, out):
    book = load_gradebook(args.book)
    out.write(render(assignment_report(book, args.as_of), args.format))
    return 0


def cmd_missing(args, out):
    book = load_gradebook(args.book)
    out.write(render(missing_work(book, args.as_of), args.format))
    return 0


def cmd_at_risk(args, out):
    book = load_gradebook(args.book)
    out.write(render(at_risk(book, args.as_of, args.below), args.format))
    return 0


def cmd_late(args, out):
    book = load_gradebook(args.book)
    out.write(render(late_work(book), args.format))
    return 0


def cmd_progress(args, out):
    book = load_gradebook(args.book)
    out.write(render_progress(progress_report(book, args.student, args.as_of)))
    return 0


def cmd_explain(args, out):
    book = load_gradebook(args.book)
    for line in explain_grade(book.course, book.grade(args.student, args.as_of)):
        print(line, file=out)
    return 0


def cmd_report_cards(args, out):
    book = load_gradebook(args.book)
    written = write_report_cards(book, args.folder, args.as_of)
    print(f"Wrote {len(written)} report cards to {args.folder}", file=out)
    return 0


def cmd_forecast(args, out):
    book = load_gradebook(args.book)
    print(describe(forecast(book, args.student, args.letter, args.as_of)), file=out)
    return 0


def cmd_sheet(args, out):
    book = load_gradebook(args.book)
    count = write_score_sheet(book, args.out)
    print(f"Wrote a score sheet for {count} students to {args.out}", file=out)
    return 0


def cmd_export_grades(args, out):
    book = load_gradebook(args.book)
    count = export_grades(book, args.out, args.as_of)
    print(f"Wrote {count} grades for {book.course.code} to {args.out}", file=out)
    return 0


def cmd_export_scores(args, out):
    book = load_gradebook(args.book)
    count = export_scores(book, args.out)
    print(f"Wrote {count} scores to {args.out}", file=out)
    return 0


def cmd_archive(args, out):
    book = load_gradebook(args.book)
    out_path = Path(args.out)
    scratch = out_path.with_name(out_path.stem + "-files")
    names = archive_term(book, out_path, scratch)
    print(f"Archived {len(names)} files to {args.out}", file=out)
    return 0


def cmd_check(args, out):
    problems = check_gradebook(load_gradebook(args.book))
    for problem in problems:
        print(problem, file=out)
    if problems:
        return EXIT_PROBLEMS
    print("No problems found", file=out)
    return 0


def cmd_day(args, out):
    try:
        when = date.fromisoformat(args.date)
    except ValueError:
        raise ConfigError(f"cannot read date {args.date}; write it as YYYY-MM-DD") from None
    print(load_calendar(args.calendar).day_of(when), file=out)
    return 0


def cmd_date(args, out):
    print(load_calendar(args.calendar).date_of(args.day).isoformat(), file=out)
    return 0


def cmd_transcript(args, out):
    out.write(render_transcript(build_transcript(args.student, args.files)))
    return 0
