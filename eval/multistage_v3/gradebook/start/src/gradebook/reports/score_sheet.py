"""Score sheets: a CSV for a teacher to fill in by hand and import with `import sheet`.

One row per student, one column per assignment in due order. Scores already on
record are filled in, so a sheet can be printed, corrected and imported again.
"""
import csv
from pathlib import Path

from ..storage.csv_util import EXCUSED


def write_score_sheet(book, path):
    """Write the sheet to `path` and return how many student rows it has."""
    assignments = book.course.ordered_assignments()
    students = book.students
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["student_id"] + [a.assignment_id for a in assignments])
        for student in students:
            cells = [_cell(book.sheet.get(student.student_id, a.assignment_id)) for a in assignments]
            writer.writerow([student.student_id] + cells)
    return len(students)


def _cell(score):
    if score is None or score.missing:
        return ""
    if score.excused:
        return EXCUSED
    return f"{score.points:g}"
