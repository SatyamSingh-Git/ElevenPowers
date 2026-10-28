"""Reports on who needs attention: missing work, and students below a percent."""
from .tables import Table

MISSING_COLUMNS = ("student_id", "name", "assignment_id", "due_day", "days_overdue")
AT_RISK_COLUMNS = ("student_id", "name", "percent", "letter", "missing")


def missing_work(book, as_of):
    """Every assignment due by `as_of` that a student has neither handed in nor been excused from."""
    rows = []
    for student in sorted(book.students, key=lambda s: s.sort_key()):
        for assignment in book.course.ordered_assignments():
            if assignment.due_day > as_of:
                continue
            if _unanswered(book.sheet.get(student.student_id, assignment.assignment_id)):
                rows.append([student.student_id, student.display_name, assignment.assignment_id,
                             str(assignment.due_day), str(as_of - assignment.due_day)])
    return Table(
        title=f"{book.course.code} missing work as of day {as_of}",
        columns=MISSING_COLUMNS,
        rows=rows,
        notes=[f"{len(rows)} missing"],
        numeric=frozenset({"due_day", "days_overdue"}),
    )


def at_risk(book, as_of, below):
    """Students whose percent as of `as_of` is under `below`, lowest first."""
    decimals = book.course.grade_decimals
    flagged = []
    for student, grade in book.grades(as_of):
        if grade.percent is None or grade.percent >= below:
            continue
        missing = sum(1 for assignment in book.course.due_by(as_of)
                      if _unanswered(book.sheet.get(student.student_id, assignment.assignment_id)))
        flagged.append((grade.percent, student, grade, missing))
    flagged.sort(key=lambda entry: (entry[0], entry[1].sort_key()))
    rows = [[student.student_id, student.display_name, f"{percent:.{decimals}f}", grade.letter, str(missing)]
            for percent, student, grade, missing in flagged]
    return Table(
        title=f"{book.course.code} students below {below:g}% as of day {as_of}",
        columns=AT_RISK_COLUMNS,
        rows=rows,
        numeric=frozenset({"percent", "missing"}),
    )


def _unanswered(score):
    return score is None or score.missing
