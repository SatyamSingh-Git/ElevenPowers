"""What a student needs on the work still to come to finish with a given letter."""
from dataclasses import dataclass
from fractions import Fraction

from ..errors import GradebookError
from ..grading.calculator import compute_grade
from ..grading.scales import get_scale
from ..model.scores import Score

# Needed percents are searched in tenths of a percent.
STEPS = 1000


@dataclass(frozen=True)
class Forecast:
    student_id: str
    letter: str
    target: float  # the letter's minimum percent
    remaining: tuple  # ids of the assignments still to come
    needed: float | None  # percent needed on each remaining assignment; None when out of reach

    @property
    def reachable(self):
        return self.needed is not None


def forecast(book, student_id, letter, as_of):
    """The even percent needed on everything due after `as_of` to end the course with `letter`.

    Excused work stays excused, and work already scored keeps its score even if
    it is due later. The answer is rounded up to a tenth of a percent.
    """
    book.student(student_id)
    course = book.course
    scale = get_scale(course.scale)
    if letter not in scale.letters():
        raise GradebookError(f"{letter} is not a letter on the {scale.name} scale")
    target = scale.minimum(letter)
    remaining = tuple(
        assignment for assignment in course.ordered_assignments()
        if assignment.due_day > as_of and book.sheet.get(student_id, assignment.assignment_id) is None
    )
    ids = tuple(assignment.assignment_id for assignment in remaining)

    def reaches(steps):
        sheet = book.sheet.copy()
        for assignment in remaining:
            points = Fraction(str(assignment.max_points)) * steps / STEPS
            sheet.set(student_id, assignment.assignment_id, Score(float(points)))
        final = compute_grade(course, sheet, student_id).percent
        return final is not None and final >= target

    if reaches(0):
        return Forecast(student_id, letter, target, ids, 0.0)
    if not remaining or not reaches(STEPS):
        return Forecast(student_id, letter, target, ids, None)
    low, high = 0, STEPS
    while high - low > 1:
        middle = (low + high) // 2
        if reaches(middle):
            high = middle
        else:
            low = middle
    return Forecast(student_id, letter, target, ids, high / 10)


def describe(result):
    if result.needed is None:
        return f"{result.student_id} cannot reach {result.letter} ({result.target:g}%) any more"
    if result.needed == 0:
        return f"{result.student_id} keeps {result.letter} ({result.target:g}%) even with no more work"
    count = len(result.remaining)
    return (f"{result.student_id} needs {result.needed:g}% on each of the {count} remaining"
            f" assignments to reach {result.letter} ({result.target:g}%)")
