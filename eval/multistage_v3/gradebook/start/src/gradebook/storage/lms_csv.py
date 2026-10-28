"""Gradebook exports from the school's LMS.

The LMS writes one row per student with columns `ID` and `Student`, then one
column per assignment headed `<title> (<assignment id>)`. Its first data row,
named `Points Possible`, gives each assignment's points; they must match the
course. Columns that are not assignments, such as `Section`, are ignored.
"""
import re

from ..errors import ImportFailed
from ..grading.rounding import exact
from .csv_util import parse_cell, read_table
from .importers import ImportSummary, at_line, importer

ASSIGNMENT_HEADER = re.compile(r"\(([^()]+)\)\s*$")
POINTS_POSSIBLE = "Points Possible"


@importer("lms")
def import_lms(book, path):
    header, rows = read_table(path, ("ID", "Student"))
    columns = {}
    for column in header:
        match = ASSIGNMENT_HEADER.search(column)
        if match:
            assignment_id = match.group(1).strip()
            if not book.course.has_assignment(assignment_id):
                raise ImportFailed(f"{path.name}: unknown assignment {assignment_id}")
            columns[column] = assignment_id
    recorded = 0
    for line, row in rows:
        if row["Student"] == POINTS_POSSIBLE:
            _check_points_possible(book.course, row, columns, path)
            continue
        student_id = row["ID"]
        if not student_id:
            continue
        for column, assignment_id in columns.items():
            kind, points = parse_cell(row[column], line)
            if kind == "blank":
                continue
            if kind == "excused":
                at_line(line, lambda: book.excuse(student_id, assignment_id))
            else:
                at_line(line, lambda: book.record_score(student_id, assignment_id, points,
                                                        book.submitted_day(student_id, assignment_id)))
            recorded += 1
    return ImportSummary("lms", len(rows), recorded)


def _check_points_possible(course, row, columns, path):
    for column, assignment_id in columns.items():
        if not row[column]:
            continue
        expected = course.assignment(assignment_id).max_points
        try:
            listed = exact(row[column])
        except ValueError:
            raise ImportFailed(f"{path.name}: cannot read points possible {row[column]}") from None
        if listed != exact(expected):
            raise ImportFailed(f"{path.name}: {assignment_id} is out of {row[column]} in the LMS"
                               f" but {expected:g} in the course")
