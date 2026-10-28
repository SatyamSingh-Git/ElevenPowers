"""Course grades: one student's scores, through the course's rules, to a percent and a letter.

For each category, the assignments due by `as_of` count (all of them when it
is None). Excused work is left out, missing work counts as zero, late work goes
through the course's late rule, and then the category's `drop_lowest` scores
are dropped. The scoring policy combines the categories, the result is rounded
half up to `grade_decimals`, and the letter comes from the course's scale.
"""
from dataclasses import dataclass
from fractions import Fraction

from .late import days_late, get_late_rule
from .policies import get_policy
from .results import CategoryResult, CourseGrade
from .rounding import exact, round_half_up
from .scales import get_scale


@dataclass(frozen=True)
class _Counted:
    assignment_id: str
    earned: Fraction
    possible: Fraction


def compute_grade(course, sheet, student_id, as_of=None):
    results = tuple(_category_result(course, category, sheet, student_id, as_of)
                    for category in course.categories)
    combined = get_policy(course.policy)(results)
    if combined is None:
        return CourseGrade(student_id, None, None, results)
    percent = round_half_up(combined, course.grade_decimals)
    return CourseGrade(student_id, percent, get_scale(course.scale).letter_for(percent), results)


def _category_result(course, category, sheet, student_id, as_of):
    counted = _drop_lowest(list(_counted_items(course, category, sheet, student_id, as_of)),
                           category.drop_lowest)
    earned = sum((item.earned for item in counted), Fraction(0))
    possible = sum((item.possible for item in counted), Fraction(0))
    percent = round_half_up(earned / possible * 100, course.grade_decimals) if possible else None
    return CategoryResult(category.name, exact(category.weight), earned, possible, percent)


def _counted_items(course, category, sheet, student_id, as_of):
    rule = get_late_rule(course.late_rule)
    for assignment in course.assignments_in(category.name):
        if as_of is not None and assignment.due_day > as_of:
            continue
        score = sheet.get(student_id, assignment.assignment_id)
        if score is not None and score.excused:
            continue
        possible = exact(assignment.max_points)
        if score is None or score.points is None:
            earned = Fraction(0)
        else:
            late = days_late(assignment.due_day, score.submitted_day)
            earned = rule(exact(score.points), possible, late, course.late)
        yield _Counted(assignment.assignment_id, earned, possible)


def _drop_lowest(items, count):
    """Drop up to `count` of the lowest scores, always keeping at least one."""
    count = min(count, len(items) - 1)
    if count <= 0:
        return items
    ranked = sorted(items, key=lambda item: item.earned)
    return ranked[count:]
