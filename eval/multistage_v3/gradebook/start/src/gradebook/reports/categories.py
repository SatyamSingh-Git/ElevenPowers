"""The category report: the class's standing in each grading category."""
from ..grading.rounding import exact, round_half_up
from .tables import Table

COLUMNS = ("category", "weight", "drop_lowest", "graded", "mean", "high", "low")


def category_report(book, as_of=None):
    course = book.course
    decimals = course.grade_decimals
    grades = [grade for _, grade in book.grades(as_of)]
    rows = []
    for category in course.categories:
        percents = [exact(result.exact_percent) for grade in grades
                    for result in grade.categories if result.name == category.name and result.graded]
        if percents:
            mean = sum(percents) / len(percents)
            spread = [f"{round_half_up(value, decimals):.{decimals}f}"
                      for value in (mean, max(percents), min(percents))]
        else:
            spread = ["", "", ""]
        rows.append([category.name, f"{category.weight:g}", str(category.drop_lowest),
                     str(len(percents)), *spread])
    return Table(
        title=f"{course.code} categories",
        columns=COLUMNS,
        rows=rows,
        numeric=frozenset(COLUMNS[1:]),
    )
