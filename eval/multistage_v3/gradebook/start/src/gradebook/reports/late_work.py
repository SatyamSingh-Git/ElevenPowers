"""The late work report: every late submission and what the late rule took off."""
from ..grading.late import days_late, get_late_rule
from ..grading.rounding import exact
from .tables import Table

COLUMNS = ("student_id", "name", "assignment_id", "days_late", "points", "kept")


def late_work(book):
    course = book.course
    rule = get_late_rule(course.late_rule)
    rows = []
    for student in sorted(book.students, key=lambda s: s.sort_key()):
        for assignment in course.ordered_assignments():
            score = book.sheet.get(student.student_id, assignment.assignment_id)
            if score is None or score.points is None:
                continue
            late = days_late(assignment.due_day, score.submitted_day)
            if not late:
                continue
            kept = rule(exact(score.points), exact(assignment.max_points), late, course.late)
            rows.append([student.student_id, student.display_name, assignment.assignment_id,
                         str(late), f"{score.points:g}", f"{float(kept):g}"])
    return Table(
        title=f"{course.code} late work ({course.late_rule})",
        columns=COLUMNS,
        rows=rows,
        notes=[f"{len(rows)} late submissions"],
        numeric=frozenset({"days_late", "points", "kept"}),
    )
