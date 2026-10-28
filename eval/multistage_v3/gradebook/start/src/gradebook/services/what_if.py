"""What-if weights: the class's grades as they would be under different category weights.

Teachers use it before changing a course's weights mid-term, to see who
would move a letter. Nothing in the gradebook is changed.
"""
from dataclasses import replace

from ..errors import ConfigError
from ..grading.calculator import compute_grade
from ..reports.tables import Table
from ..storage.course_config import WEIGHT_TOTAL

COLUMNS = ("student_id", "name", "percent", "letter", "new_percent", "new_letter")


def parse_weights(text):
    """`homework=30,quizzes=30,exams=40` as a dict of category to weight."""
    weights = {}
    for part in text.split(","):
        name, _, value = part.partition("=")
        try:
            weights[name.strip()] = float(value)
        except ValueError:
            raise ConfigError(f"cannot read weight {part.strip()}; write category=weight") from None
    return weights


def reweighted(course, weights):
    names = [category.name for category in course.categories]
    unknown = sorted(set(weights) - set(names))
    if unknown:
        raise ConfigError(f"no category named {unknown[0]}")
    missing = [name for name in names if name not in weights]
    if missing:
        raise ConfigError(f"give a weight for {missing[0]}")
    if sum(weights.values()) != WEIGHT_TOTAL:
        raise ConfigError(f"category weights add up to {sum(weights.values()):g}, not {WEIGHT_TOTAL}")
    categories = tuple(replace(category, weight=weights[category.name]) for category in course.categories)
    return replace(course, policy="weighted", categories=categories)


def what_if(book, weights, as_of=None):
    course = book.course
    other = reweighted(course, weights)
    decimals = course.grade_decimals
    rows = []
    for student, grade in sorted(book.grades(as_of), key=lambda pair: pair[0].sort_key()):
        moved = compute_grade(other, book.sheet, student.student_id, as_of)
        rows.append([student.student_id, student.display_name,
                     _percent(grade.percent, decimals), grade.letter or "-",
                     _percent(moved.percent, decimals), moved.letter or "-"])
    changed = sum(1 for row in rows if row[3] != row[5])
    return Table(
        title=f"{course.code} with weights " + ", ".join(f"{k} {v:g}" for k, v in weights.items()),
        columns=COLUMNS,
        rows=rows,
        notes=[f"{changed} letter(s) would change"],
        numeric=frozenset({"percent", "new_percent"}),
    )


def _percent(value, decimals):
    return "" if value is None else f"{value:.{decimals}f}"
