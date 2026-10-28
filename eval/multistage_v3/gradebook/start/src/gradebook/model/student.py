"""Students on a course roster."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Student:
    student_id: str
    last_name: str
    first_name: str

    @property
    def display_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def sort_name(self):
        return f"{self.last_name}, {self.first_name}"

    def sort_key(self):
        return (self.last_name.casefold(), self.first_name.casefold(), self.student_id)


def student_from_row(row):
    """A Student from a mapping with student_id, last_name and first_name, trimmed."""
    return Student(
        student_id=row["student_id"].strip(),
        last_name=row["last_name"].strip(),
        first_name=row["first_name"].strip(),
    )
