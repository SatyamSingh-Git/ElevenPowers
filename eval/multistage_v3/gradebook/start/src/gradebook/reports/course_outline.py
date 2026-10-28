"""The course outline: what a course file says, laid out for students and parents."""
from dataclasses import asdict

from .tables import Table

COLUMNS = ("due_day", "assignment_id", "title", "category", "points")


def course_outline(course):
    rows = [[str(a.due_day), a.assignment_id, a.title, a.category, f"{a.max_points:g}"]
            for a in course.ordered_assignments()]
    return Table(
        title=f"{course.code} {course.title}" + (f" ({course.term})" if course.term else ""),
        columns=COLUMNS,
        rows=rows,
        notes=_notes(course),
        numeric=frozenset({"due_day", "points"}),
    )


def _notes(course):
    notes = [f"Credits: {course.credits:g}", f"Scoring policy: {course.policy}",
             f"Letter scale: {course.scale}"]
    for category in course.categories:
        parts = [f"weight {category.weight:g}%"] if category.weight else []
        if category.drop_lowest:
            parts.append(f"lowest {category.drop_lowest} dropped")
        count = len(course.assignments_in(category.name))
        parts.append(f"{count} assignment{'s' if count != 1 else ''}")
        notes.append(f"Category {category.name}: {', '.join(parts)}")
    settings = ", ".join(f"{key} {value:g}" for key, value in asdict(course.late).items())
    notes.append(f"Late rule: {course.late_rule} ({settings})")
    notes.append(f"Final percents are rounded to {course.grade_decimals} decimal(s)")
    return notes
