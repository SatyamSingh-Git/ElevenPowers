"""A course grade explained step by step, for a student or parent who asks how it was reached."""
from .rounding import round_half_up

DETAIL_DECIMALS = 2


def explain_grade(course, grade):
    """Lines that walk from each category's points to the final percent and letter."""
    if grade.percent is None:
        return ["Nothing has been graded yet."]
    lines = []
    graded = [result for result in grade.categories if result.graded]
    for result in grade.categories:
        if not result.graded:
            lines.append(f"{result.name}: nothing graded yet, so it does not count")
            continue
        share = _format(result.exact_percent)
        lines.append(f"{result.name}: {_format(result.earned)} of {_format(result.possible)} points = {share}%")
    if course.policy == "weighted":
        total_weight = sum(result.weight for result in graded)
        parts = [f"{_format(result.exact_percent)}% x {_format(result.weight)}" for result in graded]
        lines.append(f"Weighted: ({' + '.join(parts)}) / {_format(total_weight)}")
    else:
        earned = sum(result.earned for result in graded)
        possible = sum(result.possible for result in graded)
        lines.append(f"All categories: {_format(earned)} of {_format(possible)} points")
    lines.append(f"Final: {grade.percent:.{course.grade_decimals}f}%, rounded half up to "
                 f"{course.grade_decimals} decimal(s), which is {grade.letter} on the {course.scale} scale")
    return lines


def _format(value):
    return f"{round_half_up(value, DETAIL_DECIMALS):g}"
