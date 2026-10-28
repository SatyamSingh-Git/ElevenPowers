"""A course: its grading categories, assignments and grading settings."""
from dataclasses import dataclass

from ..errors import UnknownAssignment


@dataclass(frozen=True)
class Category:
    name: str
    weight: float
    drop_lowest: int = 0


@dataclass(frozen=True)
class Assignment:
    assignment_id: str
    title: str
    category: str
    max_points: float
    due_day: int


@dataclass(frozen=True)
class LateSettings:
    """Numbers the late rules read; which rule applies is the course's `late_rule`."""

    per_day: float
    cap: float


@dataclass(frozen=True)
class Course:
    code: str
    title: str
    term: str
    credits: float
    policy: str
    scale: str
    late_rule: str
    late: LateSettings
    grade_decimals: int
    categories: tuple
    assignments: tuple

    def category(self, name):
        for category in self.categories:
            if category.name == name:
                return category
        raise KeyError(name)

    def assignment(self, assignment_id):
        for assignment in self.assignments:
            if assignment.assignment_id == assignment_id:
                return assignment
        raise UnknownAssignment(assignment_id)

    def has_assignment(self, assignment_id):
        return any(a.assignment_id == assignment_id for a in self.assignments)

    def assignments_in(self, category_name):
        return [a for a in self.assignments if a.category == category_name]

    def ordered_assignments(self):
        """Assignments by due day, then id: the order sheets and reports list them in."""
        return sorted(self.assignments, key=lambda a: (a.due_day, a.assignment_id))

    def due_by(self, day):
        if day is None:
            return list(self.assignments)
        return [a for a in self.assignments if a.due_day <= day]
