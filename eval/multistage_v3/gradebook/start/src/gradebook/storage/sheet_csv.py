"""Filled-in score sheets: one row per student, one column per assignment.

Cells use the same values as score files: blank, EX or points. A sheet carries
no submission days, so a score that was already on record keeps its day.
"""
from ..errors import ImportFailed
from .csv_util import parse_cell, read_table
from .importers import ImportSummary, at_line, importer

ID_COLUMN = "student_id"


@importer("sheet")
def import_sheet(book, path):
    header, rows = read_table(path, (ID_COLUMN,))
    assignment_ids = [column for column in header if column != ID_COLUMN]
    for assignment_id in assignment_ids:
        if not book.course.has_assignment(assignment_id):
            raise ImportFailed(f"{path.name}: unknown assignment {assignment_id}")
    recorded = 0
    for line, row in rows:
        student_id = row[ID_COLUMN]
        for assignment_id in assignment_ids:
            kind, points = parse_cell(row[assignment_id], line)
            if kind == "blank":
                continue
            if kind == "excused":
                at_line(line, lambda: book.excuse(student_id, assignment_id))
            else:
                at_line(line, lambda: book.record_score(student_id, assignment_id, points,
                                                        book.submitted_day(student_id, assignment_id)))
            recorded += 1
    return ImportSummary("sheet", len(rows), recorded)
