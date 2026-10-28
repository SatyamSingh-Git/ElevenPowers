"""A student's progress report: each assignment's status and each category's standing.

The report lists every assignment, including the ones that do not count:
upcoming work, excused work and the scores drop_lowest removed.
"""
from dataclasses import dataclass
from fractions import Fraction

from ..grading.late import days_late, get_late_rule
from ..grading.rounding import exact, round_half_up

COUNTED = ("scored", "late", "missing")


@dataclass(frozen=True)
class ProgressItem:
    assignment_id: str
    title: str
    due_day: int
    earned: float | None  # after any late penalty; None for upcoming or excused work
    possible: float
    status: str  # scored, late, missing, excused, dropped or upcoming


@dataclass(frozen=True)
class CategoryProgress:
    name: str
    weight: float
    percent: float | None
    items: tuple


@dataclass(frozen=True)
class ProgressReport:
    student_id: str
    name: str
    course: str
    percent: float | None
    letter: str | None
    basis: str
    categories: tuple

    def category(self, name):
        for category in self.categories:
            if category.name == name:
                return category
        raise KeyError(name)

    def item(self, assignment_id):
        for category in self.categories:
            for item in category.items:
                if item.assignment_id == assignment_id:
                    return item
        raise KeyError(assignment_id)


@dataclass
class _Line:
    assignment: object
    status: str
    earned: Fraction | None
    possible: Fraction


def progress_report(book, student_id, as_of=None):
    student = book.student(student_id)
    course = book.course
    grade = book.grade(student_id, as_of)
    categories = tuple(_category_progress(course, category, book.sheet, student_id, as_of)
                       for category in course.categories)
    basis = _BASES[course.policy](course, categories)
    return ProgressReport(student_id, student.display_name, course.code, grade.percent, grade.letter,
                          basis, categories)


def _category_progress(course, category, sheet, student_id, as_of):
    rule = get_late_rule(course.late_rule)
    lines = []
    for assignment in course.assignments_in(category.name):
        score = sheet.get(student_id, assignment.assignment_id)
        possible = exact(assignment.max_points)
        if as_of is not None and assignment.due_day > as_of:
            lines.append(_Line(assignment, "upcoming", None, possible))
        elif score is not None and score.excused:
            lines.append(_Line(assignment, "excused", None, possible))
        elif score is None or score.points is None:
            lines.append(_Line(assignment, "missing", Fraction(0), possible))
        else:
            late = days_late(assignment.due_day, score.submitted_day)
            earned = rule(exact(score.points), possible, late, course.late)
            lines.append(_Line(assignment, "late" if late else "scored", earned, possible))
    for line in _lowest(lines, category.drop_lowest):
        line.status = "dropped"
    counted = [line for line in lines if line.status in COUNTED]
    possible = sum((line.possible for line in counted), Fraction(0))
    earned = sum((line.earned for line in counted), Fraction(0))
    percent = round_half_up(earned / possible * 100, course.grade_decimals) if possible else None
    items = tuple(
        ProgressItem(line.assignment.assignment_id, line.assignment.title, line.assignment.due_day,
                     None if line.earned is None else float(line.earned), float(line.possible), line.status)
        for line in lines
    )
    return CategoryProgress(category.name, category.weight, percent, items)


def _lowest(lines, count):
    """The lines drop_lowest removes: the lowest scores, always keeping at least one."""
    counted = [line for line in lines if line.status in COUNTED]
    count = min(count, len(counted) - 1)
    if count <= 0:
        return []
    return sorted(counted, key=lambda line: line.earned)[:count]


def _weighted_basis(course, categories):
    parts = ", ".join(f"{category.name} {category.weight:g}%" for category in categories)
    return f"Weighted categories: {parts}"


def _points_basis(course, categories):
    counted = [item for category in categories for item in category.items if item.status in COUNTED]
    earned = sum(item.earned for item in counted)
    possible = sum(item.possible for item in counted)
    return f"Total points: {earned:g} of {possible:g}"


# How each scoring policy's grade is explained at the top of the report.
_BASES = {
    "weighted": _weighted_basis,
    "points": _points_basis,
}


def render_progress(report):
    grade = "no grade yet" if report.percent is None else f"{report.percent:g}% ({report.letter})"
    out = [f"Progress for {report.name} ({report.student_id}) in {report.course}: {grade}",
           report.basis, ""]
    for category in report.categories:
        standing = "-" if category.percent is None else f"{category.percent:g}%"
        out.append(f"{category.name}: {standing}")
        for item in category.items:
            earned = "" if item.earned is None else f"{item.earned:g}/{item.possible:g}"
            out.append(f"  {item.assignment_id:<8} day {item.due_day:>3}  {earned:>9}  {item.status}")
    return "\n".join(out) + "\n"
