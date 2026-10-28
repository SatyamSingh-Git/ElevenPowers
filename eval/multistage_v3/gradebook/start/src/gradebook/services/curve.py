"""Curving one assignment's scores.

Either every score gains the same number of points, or every score is scaled
so that the highest becomes a chosen number of points. Curved points never go
above the assignment's maximum and are kept to two decimals. Missing and
excused work is left as it is, and so is each score's submission day.
"""
from ..errors import GradebookError
from ..grading.rounding import exact, round_half_up
from ..model.scores import Score

CURVE_DECIMALS = 2


def curve_assignment(book, assignment_id, *, add=None, top=None):
    """Apply one curve and return how many scores changed."""
    if (add is None) == (top is None):
        raise GradebookError("curve with exactly one of add or top")
    assignment = book.course.assignment(assignment_id)
    scored = {sid: score for sid, score in book.sheet.for_assignment(assignment_id).items()
              if score.points is not None}
    if not scored:
        return 0
    maximum = exact(assignment.max_points)
    if add is not None:
        if add < 0:
            raise GradebookError("a curve cannot take points away")

        def curved(points):
            return points + exact(add)
    else:
        highest = max(exact(score.points) for score in scored.values())
        if not 0 < top <= assignment.max_points:
            raise GradebookError(f"top must be above 0 and at most {assignment.max_points:g}")
        if highest == 0:
            raise GradebookError(f"{assignment_id} has no points to scale")

        def curved(points):
            return points * exact(top) / highest
    changed = 0
    for student_id, score in sorted(scored.items()):
        points = round_half_up(min(curved(exact(score.points)), maximum), CURVE_DECIMALS)
        if points != score.points:
            book.sheet.set(student_id, assignment_id, Score(points, score.submitted_day))
            changed += 1
    return changed
