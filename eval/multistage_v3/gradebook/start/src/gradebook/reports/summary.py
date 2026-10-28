"""The class report: every student's course grade, with class statistics underneath."""
from ..grading.scales import get_scale
from ..services.statistics import class_statistics
from .tables import Table

COLUMNS = ("student_id", "name", "percent", "letter")


def class_summary(book, as_of=None):
    course = book.course
    graded = sorted(book.grades(as_of), key=lambda pair: pair[0].sort_key())
    rows = [_summary_row(student, grade, course.grade_decimals) for student, grade in graded]
    stats = class_statistics([grade for _, grade in graded], get_scale(course.scale), course.grade_decimals)
    return Table(
        title=f"{course.code} {course.title}",
        columns=COLUMNS,
        rows=rows,
        notes=_notes(stats, course.grade_decimals),
        numeric=frozenset({"percent"}),
    )


def _summary_row(student, grade, decimals):
    percent = "" if grade.percent is None else f"{grade.percent:.{decimals}f}"
    return [student.student_id, student.display_name, percent, grade.letter or ""]


def _notes(stats, decimals):
    if not stats.graded:
        return [f"Students: {stats.students}, none graded yet"]
    letters = ", ".join(f"{letter} {count}" for letter, count in stats.letters.items() if count)
    return [
        f"Students: {stats.students}, graded: {stats.graded}",
        f"Class average: {stats.mean:.{decimals}f}",
        f"Median: {stats.median:.{decimals}f}",
        f"Range: {stats.lowest:.{decimals}f} to {stats.highest:.{decimals}f}",
        f"Letters: {letters}",
    ]
