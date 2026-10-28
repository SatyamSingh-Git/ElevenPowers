"""The assignment report: how the class did on each assignment.

Percents here are raw scores out of the assignment's points, before late
penalties, so a teacher sees how well the work itself went.
"""
from ..grading.rounding import exact, round_half_up
from .tables import Table

COLUMNS = ("assignment_id", "title", "category", "due_day", "scored", "missing", "excused",
           "mean", "high", "low")


def assignment_report(book, as_of=None):
    course = book.course
    roster = [student.student_id for student in book.students]
    rows = []
    for assignment in course.ordered_assignments():
        if as_of is not None and assignment.due_day > as_of:
            continue
        scores = book.sheet.for_assignment(assignment.assignment_id)
        excused = sum(1 for sid in roster if sid in scores and scores[sid].excused)
        points = [scores[sid].points for sid in roster
                  if sid in scores and scores[sid].points is not None]
        missing = len(roster) - excused - len(points)
        rows.append([
            assignment.assignment_id,
            assignment.title,
            assignment.category,
            str(assignment.due_day),
            str(len(points)),
            str(missing),
            str(excused),
            *_spread(points, assignment.max_points, course.grade_decimals),
        ])
    return Table(
        title=f"{course.code} assignments",
        columns=COLUMNS,
        rows=rows,
        numeric=frozenset({"due_day", "scored", "missing", "excused", "mean", "high", "low"}),
    )


def _spread(points, max_points, decimals):
    if not points:
        return ["", "", ""]
    possible = exact(max_points)
    percents = [exact(p) / possible * 100 for p in points]
    mean = sum(percents) / len(percents)
    return [f"{round_half_up(value, decimals):.{decimals}f}" for value in (mean, max(percents), min(percents))]
