"""What grading produces for one student in one course."""
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class CategoryResult:
    name: str
    weight: Fraction
    earned: Fraction
    possible: Fraction
    percent: float | None  # rounded to the course's grade_decimals; None when nothing counts yet

    @property
    def graded(self):
        return self.possible > 0

    @property
    def exact_percent(self):
        return self.earned / self.possible * 100


@dataclass(frozen=True)
class CourseGrade:
    student_id: str
    percent: float | None
    letter: str | None
    categories: tuple

    @property
    def graded(self):
        return self.percent is not None

    def category(self, name):
        for result in self.categories:
            if result.name == name:
                return result
        raise KeyError(name)
