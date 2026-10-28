"""The term grades file: each student's course grade, as posted to the registrar."""
import csv
from pathlib import Path

COLUMNS = ("student_id", "name", "course", "credits", "percent", "letter")
DELIMITER = ","


def export_grades(book, path, as_of=None):
    """Write every student's grade to `path` and return how many rows were written."""
    grades = book.grades(as_of)
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter=DELIMITER, lineterminator="\n")
        writer.writerow(COLUMNS)
        for student, grade in grades:
            writer.writerow(_grade_row(book.course, student, grade))
    return len(grades)


def _grade_row(course, student, grade):
    percent = "" if grade.percent is None else f"{grade.percent:.1f}"
    return [student.student_id, student.display_name, course.code, f"{course.credits:g}",
            percent, grade.letter or ""]
