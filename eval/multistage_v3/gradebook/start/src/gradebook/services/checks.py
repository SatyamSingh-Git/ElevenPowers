"""Checks a gradebook file can fail after it was edited by hand.

Scores recorded through the gradebook are always valid; a saved file restores
scores without checking them, so `gradebook check` looks for what an edit
could have broken.
"""


def check_gradebook(book):
    """Every problem found, as messages in a stable order; empty when the book is sound."""
    problems = []
    roster = {student.student_id for student in book.students}
    known = {assignment.assignment_id: assignment for assignment in book.course.assignments}
    for student_id, assignment_id, score in book.sheet.items():
        where = f"{student_id}/{assignment_id}"
        if student_id not in roster:
            problems.append(f"{where}: score for a student not on the roster")
        assignment = known.get(assignment_id)
        if assignment is None:
            problems.append(f"{where}: score for an assignment the course does not have")
            continue
        if score.excused and score.points is not None:
            problems.append(f"{where}: excused but also has points")
        if score.points is not None and not 0 <= score.points <= assignment.max_points:
            problems.append(f"{where}: points {score.points:g} outside 0 to {assignment.max_points:g}")
        if score.submitted_day is not None and score.submitted_day < 1:
            problems.append(f"{where}: submitted on day {score.submitted_day}, before the term")
    for category in book.course.categories:
        if not book.course.assignments_in(category.name):
            problems.append(f"category {category.name} has no assignments")
    return problems
